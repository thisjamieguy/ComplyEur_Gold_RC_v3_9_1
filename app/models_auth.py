from datetime import datetime, timedelta

# db will be set via init_db
db = None

def init_db(database):
    global db
    db = database

# User class will be created after db is initialized
# We need to define it as a function that creates the class
def get_user_model():
    if db is None:
        raise RuntimeError("db not initialized. Call init_db() first.")
    
    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(64), unique=True, nullable=False, index=True)
        password_hash = db.Column(db.String(256), nullable=False)
        mfa_secret = db.Column(db.String(32), nullable=True)
        role = db.Column(db.String(32), default='employee', nullable=False)  # RBAC role
        oauth_provider = db.Column(db.String(32), nullable=True)  # 'google', 'microsoft', or None
        oauth_id = db.Column(db.String(128), nullable=True)  # Provider user ID
        created_at = db.Column(db.DateTime, default=datetime.utcnow)
        last_login_at = db.Column(db.DateTime, nullable=True)
        failed_attempts = db.Column(db.Integer, default=0)
        locked_until = db.Column(db.DateTime, nullable=True)


        def is_locked(self):
            return self.locked_until and datetime.utcnow() < self.locked_until


        def record_failed_attempt(self):
            self.failed_attempts = (self.failed_attempts or 0) + 1
            if self.failed_attempts >= 5:
                # Exponential backoff: 15m * 2^(n-5) capped to 24h
                exponent = max(0, self.failed_attempts - 5)
                minutes = min(15 * (2 ** exponent), 24*60)
                self.locked_until = datetime.utcnow() + timedelta(minutes=minutes)


        def reset_failed_attempts(self):
            self.failed_attempts = 0
            self.locked_until = None
    
    return User
