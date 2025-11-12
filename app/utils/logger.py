import logging, os
from logging.handlers import RotatingFileHandler


def get_auth_logger():
    os.makedirs("logs", exist_ok=True)
    handler = RotatingFileHandler("logs/auth.log", maxBytes=512000, backupCount=5)
    fmt = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
    handler.setFormatter(fmt)
    logger = logging.getLogger("auth")
    if not logger.handlers:
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def redact_username(u):
    if not u: return "<blank>"
    if len(u) <= 2: return "*"*len(u)
    return u[0] + "*"*(len(u)-2) + u[-1]

