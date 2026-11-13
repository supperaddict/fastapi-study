import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from database import get_session
from models import User
from security import SECRET_KEY, ALGORITHM


def get_pagination(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
):
    return {
        "offset": (page - 1) * size,
        "limit": size,
    }


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_session),
):
    unauthorized = HTTPException(
        status_code=401,
        detail="登录凭证无效或已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["sub", "exp"]},
        )

        subject = payload["sub"]

        if not isinstance(subject, str):
            raise unauthorized

        user_id = int(subject)

    except (InvalidTokenError, ValueError, TypeError):
        raise unauthorized

    user = session.get(User, user_id)

    if user is None or payload.get("ver") != user.auth_version:
        raise unauthorized

    return user


def require_self(
    user_id: int,
    current_user: User = Depends(get_current_user),
):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="只能操作自己的账号",
        )

    return current_user
