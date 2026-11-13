import logging
from redis import Redis
from redis.exceptions import RedisError
from config import settings

logger = logging.getLogger(__name__)
redis_client = Redis.from_url(
    settings.redis_url, decode_responses=True, socket_connect_timeout=1, socket_timeout=1
)


def get_cache():
    return redis_client


def invalidate_post_cache(cache: Redis, post_id: int):
    try:
        cache.delete(f"posts:detail:{post_id}")
    except RedisError:
        logger.warning("cache_invalidation_failed post_id=%s", post_id)
