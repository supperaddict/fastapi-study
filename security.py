from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


DUMMY_HASH = hash_password("dummy-password-for-verification")

from config import settings

SECRET_KEY = settings.jwt_secret_key.get_secret_value()
ALGORITHM = "HS256"


def create_access_token(user_id: int, auth_version: int = 0) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.token_minutes)
    return jwt.encode(
        {"sub": str(user_id), "exp": expires_at, "ver": auth_version},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
