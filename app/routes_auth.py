"""Authentication routes for ComplyEur (login, logout, MFA, OAuth).

These routes depend on initialisation via `init_routes` to inject the
database handle, CSRF and rate limiter instances.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
from datetime import datetime
try:
    import pyotp
except ImportError:
    pyotp = None

try:
    import qrcode
except ImportError:
    qrcode = None
from io import BytesIO
import base64

# These will be injected by the app factory
db = None
csrf = None
limiter = None
try:
    from .forms import LoginForm, TOTPForm
    FORMS_AVAILABLE = True
except ModuleNotFoundError:
    LoginForm = TOTPForm = None
    FORMS_AVAILABLE = False

from . import models_auth
from .utils.logger import get_auth_logger, redact_username
from app.modules.auth import SessionManager, CaptchaManager


def _try_legacy_login(username: str, password: str) -> bool:
    """Attempt legacy admin login using sqlite admin table."""
    logger = get_auth_logger()
    from flask import current_app
    import sqlite3

    db_path = current_app.config.get('DATABASE')
    if not db_path:
        return False

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute('SELECT password_hash FROM admin WHERE id = 1')
        admin = cur.fetchone()
        conn.close()
    except Exception as exc:
        logger.error(f"Legacy admin lookup failed: {exc}")
        return False

    if not admin:
        return False

    normalized = (username or "").strip().lower()
    allowed = {
        (current_app.config.get('ADMIN_USERNAME') or 'admin').strip().lower(),
        'admin',
        'administrator',
        '',
    }
    admin_dict = dict(admin)
    for key in ('email', 'company_name', 'full_name'):
        value = admin_dict.get(key)
        if value:
            allowed.add(str(value).strip().lower())

    if normalized and normalized not in allowed:
        logger.info(f"LOGIN_LEGACY_USERNAME_MISMATCH uname={redact_username(username)}")
        return False

    stored = admin['password_hash'] or ''
    matched = False
    try:
        matched = verify_password(stored, password)
    except Exception:
        matched = False
    if not matched and stored == password:
        matched = True

    if matched:
        SessionManager.set_user(1, 'admin')
        session['logged_in'] = True
        session['username'] = (username or 'admin').strip() or 'admin'
        logger.info(f"LOGIN_SUCCESS_LEGACY uname={redact_username(username)}")
        return True

    return False


def init_routes(database, csrf_protect, rate_limiter):
    global db, csrf, limiter
    db = database
    csrf = csrf_protect
    limiter = rate_limiter
    
    if limiter is None:
        logger = get_auth_logger()
        logger.warning("Flask-Limiter not available; login rate limiting disabled")


def _should_require_captcha() -> bool:
    """Check if CAPTCHA should be required based on failed login attempts."""
    return session.get("failed_login_count", 0) >= 5

# Import password functions - use Hasher from services for compatibility
try:
    from app.services.hashing import Hasher
    # Create a global hasher instance for password verification
    _hasher = None
    
    def _get_hasher():
        global _hasher
        if _hasher is None:
            _hasher = Hasher()
        return _hasher
    
    def verify_password(stored_hash: str, password: str) -> bool:
        """Verify password against stored hash"""
        try:
            return _get_hasher().verify(stored_hash, password)
        except Exception:
            return False
    
    def hash_password(plain: str) -> str:
        """Hash password"""
        return _get_hasher().hash(plain)
except ImportError:
    # Fallback to legacy security module if available
    try:
        from app.security import verify_password, hash_password
    except ImportError:
        # Final fallback - basic stub functions
        def verify_password(stored_hash: str, password: str) -> bool:
            logger = get_auth_logger()
            logger.error("Password verification not available - install hashing dependencies")
            return False
        
        def hash_password(plain: str) -> str:
            raise NotImplementedError("Password hashing not available")

# Session functions - these are handled by SessionManager now
def rotate_session_id():
    """Rotate session ID"""
    SessionManager.rotate_session_id()

def session_expired() -> bool:
    """Check if session expired"""
    return SessionManager.is_expired()

def touch_session():
    """Update session activity"""
    SessionManager.touch_session()


auth_bp = Blueprint("auth", __name__)


@auth_bp.before_app_request
def enforce_session_timeouts():
    # Initialize session for CSRF token storage (needed for Flask-WTF)
    if not session.get('_permanent'):
        session.permanent = True
    
    protected = not request.path.startswith(("/login", "/static", "/setup-2fa", "/oauth"))
    if "user_id" in session and protected:
        # Use new SessionManager - it will auto-initialize missing timestamps if needed
        if SessionManager.is_expired():
            SessionManager.clear_session()
            flash("Session expired. Please sign in again.", "warning")
            return redirect(url_for("auth.login"))
        SessionManager.touch_session()
        session.permanent = True  # Ensure session persists


def _rate_limit_login(fn):
    """Apply rate limiting to login if limiter is available."""
    if limiter:
        return limiter.limit("10 per minute")(fn)
    return fn

@auth_bp.route("/login", methods=["GET","POST"])
@_rate_limit_login
def login():
    # Check for login bypass - if enabled, auto-login and redirect to dashboard
    import os
    if os.getenv('EUTRACKER_BYPASS_LOGIN') == '1':
        try:
            SessionManager.set_user(1, 'admin')
        except (ImportError, AttributeError):
            # If SessionManager not available, use legacy session
            pass
        session['logged_in'] = True
        session['user_id'] = 1
        session['username'] = 'admin'
        session['last_activity'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        session.permanent = True
        return redirect(url_for("main.dashboard"))
    
    # Rate limiting is handled via limiter.hit() calls inside the function
    # The decorator approach doesn't work when limiter is None at module load time
    logger = get_auth_logger()
    
    # Initialize session for CSRF token (Flask-WTF needs a session to store CSRF token)
    session.permanent = True
    session.modified = True  # Force session to be saved
    
    form = LoginForm() if FORMS_AVAILABLE else None
    form_data = {"username": ""}
    uname = ""
    pwd = ""

    if request.method == "POST":
        # Debug: Log that we received a POST request
        logger.debug(f"Login POST received from {request.remote_addr}")
        
        # Local math CAPTCHA verification (if required after 5 failed attempts)
        if _should_require_captcha():
            try:
                captcha_a = int(request.form.get("captcha_a", "0"))
                captcha_b = int(request.form.get("captcha_b", "0"))
                captcha_answer = int(request.form.get("captcha_answer", "-1"))
                if captcha_a + captcha_b != captcha_answer:
                    logger.info(f"LOGIN_CAPTCHA_FAIL uname={redact_username(uname) if 'uname' in locals() else 'unknown'} ip={request.remote_addr}")
                    flash("CAPTCHA verification failed. Please try again.", "danger")
                    form_data = {"username": request.form.get("username", "")}
                    return render_template(
                        "auth_login.html",
                        form=form if FORMS_AVAILABLE else None,
                        wtforms_enabled=FORMS_AVAILABLE,
                        form_data=form_data,
                        require_captcha=True,
                        captcha_a=captcha_a,
                        captcha_b=captcha_b,
                    )
            except (ValueError, TypeError):
                logger.info(f"LOGIN_CAPTCHA_INVALID ip={request.remote_addr}")
                flash("CAPTCHA verification failed. Please try again.", "danger")
                form_data = {"username": request.form.get("username", "")}
                import random
                a, b = random.randint(1, 9), random.randint(1, 9)
                return render_template(
                    "auth_login.html",
                    form=form if FORMS_AVAILABLE else None,
                    wtforms_enabled=FORMS_AVAILABLE,
                    form_data=form_data,
                    require_captcha=True,
                    captcha_a=a,
                    captcha_b=b,
                )
        
        if FORMS_AVAILABLE:
            if not form.validate_on_submit():
                # Form validation failed - show errors
                if form.errors:
                    for field, errors in form.errors.items():
                        for error in errors:
                            flash(f"{field}: {error}", "danger")
                            logger.debug(f"Form validation error: {field}={error}")
                return render_template(
                    "auth_login.html",
                    form=form,
                    wtforms_enabled=True,
                    form_data=form_data,
                )
            uname = form.username.data.strip()
            pwd = form.password.data
        else:
            uname = (request.form.get("username") or "").strip()
            pwd = request.form.get("password") or ""
            form_data["username"] = uname
            logger.debug(f"Login attempt - username: {redact_username(uname)}, has_password: {bool(pwd)}")
            if not uname:
                flash("username: Username is required", "danger")
            if not pwd:
                flash("password: Password is required", "danger")
            if not uname or not pwd:
                return render_template(
                    "auth_login.html",
                    form=None,
                    wtforms_enabled=False,
                    form_data=form_data,
                )

        # Form validated successfully - proceed with login
        # CAPTCHA verification (if enabled)
        if CaptchaManager.is_enabled():
            if not CaptchaManager.is_human():
                logger.info(f"LOGIN_CAPTCHA_FAIL uname={redact_username(uname)} ip={request.remote_addr}")
                flash("CAPTCHA verification failed. Please try again.", "danger")
                return render_template(
                    "auth_login.html",
                    form=form if FORMS_AVAILABLE else None,
                    wtforms_enabled=FORMS_AVAILABLE,
                    form_data=form_data,
                )
        
        form_data["username"] = uname
        
        # Per-username rate limiting (only if limiter is available)
        username_limit_key = f"user:{uname}"
        if limiter:
            try:
                rate_limit = current_app.config.get("RATE_PER_USERNAME", "10 per minute")
                if not limiter.hit(rate_limit, key_func=lambda: username_limit_key):
                    logger.info(f"LOGIN_RATE_LIMITED uname={redact_username(uname)} ip={request.remote_addr}")
                    flash("Too many attempts. Please try again later.", "danger")
                    return render_template(
                        "auth_login.html",
                        form=form if FORMS_AVAILABLE else None,
                        wtforms_enabled=FORMS_AVAILABLE,
                        form_data=form_data,
                    )
            except Exception:
                # If limiter check fails, log but continue
                logger.warning("Rate limiter check failed, continuing without rate limit")
        
        # Query user (handle case where db might be None - use fallback)
        user = None
        if db:
            try:
                user = models_auth.User.query.filter_by(username=uname).first()
            except Exception as e:
                logger.error(f"Database query failed: {e}")
                # Fall back to old admin table if new auth system not available
                pass
        
        if not user:
            if _try_legacy_login(uname, pwd):
                return redirect(url_for("main.dashboard"))
            if not db:
                # No SQLAlchemy backend configured and legacy failed
                flash("Invalid credentials.", "danger")
                logger.info(f"LOGIN_FAIL_LEGACY uname={redact_username(uname)} ip={request.remote_addr}")
                return render_template(
                    "auth_login.html",
                    form=form if FORMS_AVAILABLE else None,
                    wtforms_enabled=FORMS_AVAILABLE,
                    form_data=form_data,
                )

        if not user or (db and (user.is_locked() or not verify_password(user.password_hash, pwd))):
            # failed path - increment failed_login_count for local CAPTCHA
            session["failed_login_count"] = session.get("failed_login_count", 0) + 1
            
            if user and db:
                if user.is_locked():
                    logger.info(f"LOGIN_FAIL_LOCKED uname={redact_username(uname)}")
                    flash("Invalid credentials.", "danger")
                    return render_template(
                        "auth_login.html",
                        form=form if FORMS_AVAILABLE else None,
                        wtforms_enabled=FORMS_AVAILABLE,
                        form_data=form_data,
                        require_captcha=_should_require_captcha(),
                    )
                try:
                    user.record_failed_attempt()
                    db.session.commit()
                except Exception as e:
                    logger.error(f"Failed to record failed attempt: {e}")
            else:
                if _try_legacy_login(uname, pwd):
                    session["failed_login_count"] = 0  # Reset on success
                    return redirect(url_for("main.dashboard"))
            logger.info(f"LOGIN_FAIL uname={redact_username(uname)} ip={request.remote_addr}")
            flash("Invalid credentials.", "danger")
            import random
            a, b = random.randint(1, 9), random.randint(1, 9)
            return render_template(
                "auth_login.html",
                form=form if FORMS_AVAILABLE else None,
                wtforms_enabled=FORMS_AVAILABLE,
                form_data=form_data,
                require_captcha=_should_require_captcha(),
                captcha_a=a,
                captcha_b=b,
            )


        # success: reset counters
        if db and user:
            try:
                user.reset_failed_attempts()
                user.last_login_at = datetime.utcnow()
                db.session.commit()
            except Exception as e:
                logger.error(f"Failed to update user on login: {e}")

        # Use new SessionManager (only if user exists)
        if user:
            SessionManager.set_user(user.id, getattr(user, 'role', 'admin'))
            session['logged_in'] = True
            session['username'] = getattr(user, 'username', uname)
            session['user'] = getattr(user, 'username', uname)  # For util_auth compatibility
            session['user_id'] = user.id
            session["failed_login_count"] = 0  # Reset failed count on success
            
            # Check for TOTP if enabled
            if (
                pyotp
                and current_app.config.get("AUTH_TOTP_ENABLED")
                and getattr(user, 'mfa_secret', None)
            ):
                session["awaiting_totp"] = True
                return redirect(url_for("auth.login_totp"))

        return redirect(url_for("main.dashboard"))
    
    # GET request - show login form with CAPTCHA if needed
    import random
    a, b = random.randint(1, 9), random.randint(1, 9)
    return render_template(
        "auth_login.html",
        form=form if FORMS_AVAILABLE else None,
        wtforms_enabled=FORMS_AVAILABLE,
        form_data=form_data,
        require_captcha=_should_require_captcha(),
        captcha_a=a,
        captcha_b=b,
    )


@auth_bp.route("/login/totp", methods=["GET","POST"])
def login_totp():
    logger = get_auth_logger()
    if not session.get("user_id") or not session.get("awaiting_totp"):
        return redirect(url_for("auth.login"))
    if not pyotp:
        flash("Two-factor verification is unavailable. Contact your administrator.", "warning")
        session.pop("awaiting_totp", None)
        return redirect(url_for("main.dashboard"))
    # Handle case where db might not be available
    user = None
    if db:
        try:
            user = models_auth.User.query.get(session["user_id"])
        except Exception as e:
            logger.error(f"Failed to query user for TOTP: {e}")
    if not user or not getattr(user, 'mfa_secret', None):
        return redirect(url_for("auth.login"))
    form = TOTPForm() if FORMS_AVAILABLE else None
    token_value = ""
    if request.method == "POST":
        if FORMS_AVAILABLE:
            if not form.validate_on_submit():
                if form.errors:
                    for field, errors in form.errors.items():
                        for error in errors:
                            flash(f"{field}: {error}", "danger")
                return render_template(
                    "auth_login.html",
                    form=form,
                    wtforms_enabled=True,
                    totp_mode=True,
                    form_data={},
                )
            token_value = form.token.data.strip().replace(" ", "")
        else:
            token_value = (request.form.get("token") or "").strip().replace(" ", "")
            if not token_value:
                flash("token: Code is required", "danger")
                return render_template(
                    "auth_login.html",
                    form=None,
                    wtforms_enabled=False,
                    totp_mode=True,
                    form_data={},
                )

        totp = pyotp.TOTP(user.mfa_secret)
        if totp.verify(token_value, valid_window=1):
            session.pop("awaiting_totp", None)
            return redirect(url_for("main.dashboard"))
        get_auth_logger().info("TOTP_FAIL")
        flash("Invalid code.", "danger")
    return render_template(
        "auth_login.html",
        form=form if FORMS_AVAILABLE else None,
        wtforms_enabled=FORMS_AVAILABLE,
        totp_mode=True,
        form_data={},
    )


@auth_bp.route("/setup-2fa", methods=["GET","POST"])
def setup_2fa():
    logger = get_auth_logger()
    # Pretend /dashboard already checks authentication
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    if not pyotp or not qrcode:
        flash("Two-factor setup requires optional dependencies that are not installed.", "warning")
        return redirect(url_for("main.dashboard"))
    user = None
    if db:
        try:
            user = models_auth.User.query.get(session["user_id"])
        except Exception as e:
            logger.error(f"Failed to query user for 2FA setup: {e}")
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.login"))
    if request.method == "POST":
        # generate and attach secret
        secret = pyotp.random_base32()
        if db:
            try:
                user.mfa_secret = secret
                db.session.commit()
            except Exception as e:
                logger.error(f"Failed to save 2FA secret: {e}")
                flash("Failed to save 2FA secret.", "danger")
        return redirect(url_for("auth.setup_2fa"))
    # QR for current secret
    secret = getattr(user, 'mfa_secret', None) or pyotp.random_base32()
    if not getattr(user, 'mfa_secret', None) and db:
        try:
            user.mfa_secret = secret
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to save initial 2FA secret: {e}")
    issuer = "EU_Tracker"
    username = getattr(user, 'username', f'user_{session.get("user_id", "unknown")}')
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name=username, issuer_name=issuer)
    img = qrcode.make(uri)
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return render_template("auth_setup_2fa.html", secret=secret, qr_b64=b64)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    SessionManager.clear_session()
    flash("Signed out.", "info")
    return redirect(url_for("auth.login"))


# OAuth 2.0 Routes
@auth_bp.route("/oauth/login/<provider>")
def oauth_login(provider):
    """Initiate OAuth login flow"""
    from app.modules.auth import OAuthManager
    
    if provider not in ['google', 'microsoft']:
        flash("Invalid OAuth provider.", "danger")
        return redirect(url_for("auth.login"))
    
    auth_url = OAuthManager.initiate_login(provider)
    if not auth_url:
        flash("OAuth is not configured for this provider.", "warning")
        return redirect(url_for("auth.login"))
    
    return redirect(auth_url)


@auth_bp.route("/oauth/callback/<provider>")
def oauth_callback(provider):
    """Handle OAuth callback"""
    logger = get_auth_logger()
    from app.modules.auth import OAuthManager, SessionManager
    
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code or not state:
        flash("OAuth authentication failed.", "danger")
        return redirect(url_for("auth.login"))
    
    result = OAuthManager.handle_callback(code, state)
    if not result:
        flash("OAuth authentication failed.", "danger")
        return redirect(url_for("auth.login"))
    
    user_id = result['user_id']
    user = None
    if db:
        try:
            user = models_auth.User.query.get(user_id)
        except Exception as e:
            logger.error(f"Failed to query user for OAuth: {e}")
    
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.login"))
    
    # Set session
    SessionManager.set_user(user_id, getattr(user, 'role', 'admin'))
    
    # Check for MFA
    if current_app.config.get("AUTH_TOTP_ENABLED") and getattr(user, 'mfa_secret', None):
        session["awaiting_totp"] = True
        return redirect(url_for("auth.login_totp"))
    
    flash("Successfully signed in.", "success")
    return redirect(url_for("main.dashboard"))
