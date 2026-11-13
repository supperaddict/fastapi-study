from fastapi import APIRouter, Depends, HTTPException,Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_session
from schemas import LoginRequest, TokenResponse,PasswordChange
from security import DUMMY_HASH, verify_password, create_access_token,hash_password
from models import User

from dependencies import get_current_user
from schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["认证"])

@router.post("/change-password", status_code=204)
def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if (
        not current_user.hashed_password
        or not verify_password(
            data.old_password,
            current_user.hashed_password,
        )
    ):
        raise HTTPException(
            status_code=400,
            detail="旧密码错误",
        )

    if data.old_password == data.new_password:
        raise HTTPException(
            status_code=400,
            detail="新密码不能与旧密码相同",
        )

    current_user.hashed_password = hash_password(
        data.new_password
    )

    session.commit()

    return Response(status_code=204)

@router.get("/me", response_model=UserResponse)
def read_current_user(
    current_user: User = Depends(get_current_user),
):
    return current_user

@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    session: Session = Depends(get_session),
):
    statement = select(User).where(
        User.username == credentials.username
    )
    user = session.scalars(statement).first()

    stored_hash = (
        user.hashed_password
        if user is not None and user.hashed_password
        else DUMMY_HASH
    )

    password_matches = verify_password(
        credentials.password,
        stored_hash,
    )

    if (
        user is None
        or not user.hashed_password
        or not password_matches
    ):
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误",
        )


    return {
        "access_token": create_access_token(user.id),
        "token_type": "bearer",
    }