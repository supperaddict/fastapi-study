from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from redis import Redis
from cache import get_cache, invalidate_post_cache
from database import get_session
from dependencies import get_pagination, require_self
from security import hash_password
from models import User, Post
from schemas import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["用户"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user: UserCreate,
    session: Session = Depends(get_session),
):
    new_user = User(
        username=user.username,
        age=user.age,
        email=user.email,
        hashed_password=hash_password(user.password),
    )

    session.add(new_user)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="用户数据违反数据库约束，请检查用户名是否重复",
        )

    session.refresh(new_user)

    return new_user


@router.get("", response_model=list[UserResponse])
def list_users(
    pagination: dict = Depends(get_pagination),
    session: Session = Depends(get_session),
):
    statement = (
        select(User).order_by(User.id).offset(pagination["offset"]).limit(pagination["limit"])
    )

    return session.scalars(statement).all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    session: Session = Depends(get_session),
):
    user = session.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="用户不存在",
        )

    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    updates: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_self),
):

    changes = updates.model_dump(exclude_unset=True)

    if any(changes[field] is None for field in ("username", "age") if field in changes):
        raise HTTPException(
            status_code=422,
            detail="用户名、年龄不能为 null",
        )

    user = session.get(User, user_id, with_for_update=True)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="用户不存在",
        )

    for field, value in changes.items():
        setattr(user, field, value)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="用户数据违反数据库约束，请检查用户名是否重复",
        )

    session.refresh(user)

    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_self),
    cache: Redis = Depends(get_cache),
):
    user = session.get(User, user_id, with_for_update=True)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    post_ids = session.scalars(select(Post.id).where(Post.author_id == user_id)).all()
    session.delete(user)
    session.commit()
    for post_id in post_ids:
        invalidate_post_cache(cache, post_id)
    return Response(status_code=204)
