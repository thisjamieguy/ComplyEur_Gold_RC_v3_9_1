from typing import Literal


try:
    from argon2 import PasswordHasher
    _argon2_available = True
except Exception:
    _argon2_available = False

try:
    import bcrypt
    _bcrypt_available = True
except Exception:
    _bcrypt_available = False


class Hasher:
    def __init__(self, scheme: Literal['argon2', 'bcrypt'] = 'argon2'):
        self.scheme = 'argon2' if (scheme == 'argon2' and _argon2_available) else ('bcrypt' if _bcrypt_available else 'bcrypt')
        if self.scheme == 'argon2':
            self._ph = PasswordHasher()  # Reasonable defaults

    def hash(self, password: str) -> str:
        if self.scheme == 'argon2':
            return self._ph.hash(password)
        # bcrypt
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify(self, stored_hash: str, password: str) -> bool:
        if self.scheme == 'argon2':
            try:
                return self._ph.verify(stored_hash, password)
            except Exception:
                return False
        try:
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
        except Exception:
            return False




