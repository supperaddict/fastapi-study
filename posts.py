from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_session
from dependencies import get_current_user, get_pagination
from models import Post, User
from schemas import PostCreate, PostResponse, PostListItem, PostUpdate
import logging

from redis import Redis
from redis.exceptions import RedisError

from cache import get_cache


router = APIRouter(prefix="/posts", tags=["文章"])

logger = logging.getLogger(__name__)


def invalidate_post_cache(cache: Redis, post_id: int):
    try:
        cache.delete(f"posts:detail:{post_id}")
    except RedisError:
        logger.warning("文章缓存删除失败，post_id=%s", post_id)

@router.delete("/{post_id}", status_code=204)
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    cache: Redis = Depends(get_cache),
):
    post = session.get(Post, post_id, with_for_update=True)

    if post is None:
        raise HTTPException(status_code=404, detail="文章不存在")

    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="只能删除自己的文章",
        )

    session.delete(post)    
    session.commit()

    invalidate_post_cache(cache, post_id)

    return Response(status_code=204)

@router.patch("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    data: PostUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
    cache: Redis = Depends(get_cache),
):
    changes = data.model_dump(exclude_unset=True)

    if any(value is None for value in changes.values()):
        raise HTTPException(
            status_code=422,
            detail="标题和正文不能为 null",
        )

    post = session.get(Post, post_id, with_for_update=True)

    if post is None:
        raise HTTPException(status_code=404, detail="文章不存在")

    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="只能修改自己的文章",
        )

    for field, value in changes.items():
        setattr(post, field, value)

    session.commit()
    invalidate_post_cache(cache, post_id)
    session.refresh(post)

    return post

@router.get("/{post_id}", response_model=PostResponse)
def get_post(
    post_id: int,
    session: Session = Depends(get_session),
    cache: Redis = Depends(get_cache),
):
    key = f"posts:detail:{post_id}"

    try:
        cached = cache.get(key)

        if cached is not None:
            post_data = PostResponse.model_validate_json(cached)
            print("缓存命中：", post_id)
            return post_data

    except RedisError:
        logger.warning("缓存读取失败，改查数据库")

    except ValueError:
        logger.warning("缓存内容无效，改查数据库")

    post = session.get(Post, post_id)

    if post is None:
        raise HTTPException(status_code=404, detail="文章不存在")

    print("查询数据库：", post_id)

    post_data = PostResponse.model_validate(post)

    try:
        cache.set(
            key,
            post_data.model_dump_json(),
            ex=60,
        )
    except RedisError:
        logger.warning("缓存写入失败，返回数据库结果")

    return post_data

@router.get("", response_model=list[PostListItem])
def list_posts(
    pagination: dict = Depends(get_pagination),
    session: Session = Depends(get_session),
):
    statement = (
        select(
            Post.id,
            Post.title,
            Post.author_id,
            User.username.label("author_username"),
        )
        .join(User, Post.author_id == User.id)
        .order_by(Post.id.desc())
        .offset(pagination["offset"])
        .limit(pagination["limit"])
    )

    result = session.execute(statement)

    return [dict(row) for row in result.mappings()]

@router.post(
    "",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_post(
    data: PostCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    post = Post(
        title=data.title,
        content=data.content,
        author_id=current_user.id,
    )

    session.add(post)
    session.commit()
    session.refresh(post)

    return post