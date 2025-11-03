import click
from getpass import getpass
from .security import hash_password

# db and User will be injected
db = None
User = None

def init_cli(app, database, user_model):
    @app.cli.group("admin")
    def admin():
        """Admin management commands."""


    @admin.command("create")
    @click.option("--username", prompt=True)
    def create_admin(username):
        if User.query.filter_by(username=username).first():
            click.echo("User already exists.")
            return
        pw1 = getpass("New password: ")
        pw2 = getpass("Confirm password: ")
        if pw1 != pw2:
            click.echo("Passwords do not match.")
            return
        user = User(username=username, password_hash=hash_password(pw1))
        db.session.add(user)
        db.session.commit()
        click.echo(f"Created admin '{username}'.")


    @admin.command("reset-password")
    @click.option("--username", prompt=True)
    def reset_password(username):
        user = User.query.filter_by(username=username).first()
        if not user:
            click.echo("User not found.")
            return
        pw1 = getpass("New password: ")
        pw2 = getpass("Confirm password: ")
        if pw1 != pw2:
            click.echo("Passwords do not match.")
            return
        user.password_hash = hash_password(pw1)
        db.session.commit()
        click.echo("Password updated.")


    @admin.command("enable-2fa")
    @click.option("--username", prompt=True)
    def enable_2fa(username):
        import pyotp
        user = User.query.filter_by(username=username).first()
        if not user:
            click.echo("User not found.")
            return
        user.mfa_secret = pyotp.random_base32()
        db.session.commit()
        click.echo("2FA enabled and secret generated (user must scan QR on /setup-2fa).")


    @admin.command("disable-2fa")
    @click.option("--username", prompt=True)
    def disable_2fa(username):
        user = User.query.filter_by(username=username).first()
        if not user:
            click.echo("User not found.")
            return
        user.mfa_secret = None
        db.session.commit()
        click.echo("2FA disabled.")

