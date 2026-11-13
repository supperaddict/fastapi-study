import jwt
from jwt.exceptions import InvalidTokenError

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from database import get_session
from models import User
from security import SECRET_KEY, ALGORITHM

from fastapi import Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.engine import Connection

import store
from database import get_connection

def get_existing_user(user_id: int):
    if user_id not in store.users:
        raise HTTPException(
            status_code=404,
            detail="用户不存在",
        )

    return store.users[user_id]

def get_pagination(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
):
    return {
        "offset": (page - 1) * size,
        "limit": size,
    }

def get_db_user(
    user_id: int,
    connection: Connection = Depends(get_connection),
):
    result = connection.execute(
        text("""
            SELECT id, username, age
            FROM users
            WHERE id = :user_id
        """),
        {"user_id": user_id},
    )

    user = result.mappings().first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="用户不存在",
        )

    return dict(user)

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
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

    if user is None:
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