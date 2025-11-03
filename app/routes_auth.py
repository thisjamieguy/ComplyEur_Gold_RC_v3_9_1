from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
from flask_limiter.util import get_remote_address
from datetime import datetime
import pyotp, qrcode
from io import BytesIO
import base64

# These will be injected by the app factory
db = None
csrf = None
limiter = None

def init_routes(database, csrf_protect, rate_limiter):
    global db, csrf, limiter
    db = database
    csrf = csrf_protect
    limiter = rate_limiter

from . import models_auth
from .utils.logger import get_auth_logger, redact_username
from app.modules.auth import SessionManager, CaptchaManager

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
        # Use new SessionManager
        if SessionManager.is_expired():
            SessionManager.clear_session()
            flash("Session expired. Please sign in again.", "warning")
            return redirect(url_for("auth.login"))
        SessionManager.touch_session()


@auth_bp.route("/login", methods=["GET","POST"])
def login():
    # Rate limiting is handled via limiter.hit() calls inside the function
    # The decorator approach doesn't work when limiter is None at module load time
    from .forms import LoginForm, TOTPForm
    logger = get_auth_logger()
    
    # Initialize session for CSRF token (Flask-WTF needs a session to store CSRF token)
    session.permanent = True
    session.modified = True  # Force session to be saved
    
    form = LoginForm()
    if request.method == "POST":
        if not form.validate_on_submit():
            # Form validation failed - show errors
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f"{field}: {error}", "danger")
            return render_template("auth_login.html", form=form)
        
        # Form validated successfully - proceed with login
        # CAPTCHA verification (if enabled)
        if CaptchaManager.is_enabled():
            if not CaptchaManager.is_human():
                logger.info(f"LOGIN_CAPTCHA_FAIL uname={redact_username(form.username.data.strip())} ip={request.remote_addr}")
                flash("CAPTCHA verification failed. Please try again.", "danger")
                return render_template("auth_login.html", form=form)
        
        uname = form.username.data.strip()
        pwd = form.password.data
        
        # Per-username rate limiting (only if limiter is available)
        username_limit_key = f"user:{uname}"
        if limiter:
            try:
                rate_limit = current_app.config.get("RATE_PER_USERNAME", "10 per minute")
                if not limiter.hit(rate_limit, key_func=lambda: username_limit_key):
                    logger.info(f"LOGIN_RATE_LIMITED uname={redact_username(uname)} ip={request.remote_addr}")
                    flash("Too many attempts. Please try again later.", "danger")
                    return render_template("auth_login.html", form=form)
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
        
        # If new auth system not available, try legacy admin table
        if not user and not db:
            # Fallback to legacy password check from admin table
            from flask import current_app
            import sqlite3
            try:
                db_path = current_app.config.get('DATABASE')
                if db_path:
                    conn = sqlite3.connect(db_path)
                    conn.row_factory = sqlite3.Row
                    c = conn.cursor()
                    c.execute('SELECT password_hash FROM admin WHERE id = 1')
                    admin = c.fetchone()
                    conn.close()
                    if admin and verify_password(admin['password_hash'], pwd):
                        # Legacy auth success - set session
                        from app.modules.auth import SessionManager
                        SessionManager.set_user(1, 'admin')  # Default admin user
                        return redirect(url_for("main.dashboard"))
            except Exception as e:
                logger.error(f"Legacy auth fallback failed: {e}")

        if not user or (db and (user.is_locked() or not verify_password(user.password_hash, pwd))):
            # failed path
            if user and db:
                if user.is_locked():
                    logger.info(f"LOGIN_FAIL_LOCKED uname={redact_username(uname)}")
                    flash("Invalid credentials.", "danger")
                    return render_template("auth_login.html", form=form)
                try:
                    user.record_failed_attempt()
                    db.session.commit()
                except Exception as e:
                    logger.error(f"Failed to record failed attempt: {e}")
            logger.info(f"LOGIN_FAIL uname={redact_username(uname)} ip={request.remote_addr}")
            flash("Invalid credentials.", "danger")
            return render_template("auth_login.html", form=form)


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
            
            # Check for TOTP if enabled
            if current_app.config.get("AUTH_TOTP_ENABLED") and getattr(user, 'mfa_secret', None):
                session["awaiting_totp"] = True
                return redirect(url_for("auth.login_totp"))

        return redirect(url_for("main.dashboard"))
    return render_template("auth_login.html", form=form)


@auth_bp.route("/login/totp", methods=["GET","POST"])
def login_totp():
    from .forms import TOTPForm
    logger = get_auth_logger()
    if not session.get("user_id") or not session.get("awaiting_totp"):
        return redirect(url_for("auth.login"))
    # Handle case where db might not be available
    user = None
    if db:
        try:
            user = models_auth.User.query.get(session["user_id"])
        except Exception as e:
            logger.error(f"Failed to query user for TOTP: {e}")
    if not user or not getattr(user, 'mfa_secret', None):
        return redirect(url_for("auth.login"))
    form = TOTPForm()
    if request.method == "POST" and form.validate_on_submit():
        token = form.token.data.strip().replace(" ", "")
        totp = pyotp.TOTP(user.mfa_secret)
        if totp.verify(token, valid_window=1):
            session.pop("awaiting_totp", None)
            return redirect(url_for("main.dashboard"))
        else:
            get_auth_logger().info("TOTP_FAIL")
            flash("Invalid code.", "danger")
    return render_template("auth_login.html", form=form, totp_mode=True)


@auth_bp.route("/setup-2fa", methods=["GET","POST"])
def setup_2fa():
    # Pretend /dashboard already checks authentication
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
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

