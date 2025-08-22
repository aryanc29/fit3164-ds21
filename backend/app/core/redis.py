import aioredis
import json
from typing import Any, Optional
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

redis_client: Optional[aioredis.Redis] = None


async def init_redis():
    """Initialize Redis connection"""
    global redis_client
    try:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        # Test connection
        await redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        redis_client = None


async def get_redis() -> Optional[aioredis.Redis]:
    """Get Redis client"""
    return redis_client


async def cache_set(key: str, value: Any, ttl: int = None) -> bool:
    """Set value in cache"""
    if not redis_client:
        return False
    
    try:
        ttl = ttl or settings.REDIS_CACHE_TTL
        serialized_value = json.dumps(value, default=str)
        await redis_client.setex(key, ttl, serialized_value)
        return True
    except Exception as e:
        logger.error(f"Cache set failed for key {key}: {e}")
        return False


async def cache_get(key: str) -> Optional[Any]:
    """Get value from cache"""
    if not redis_client:
        return None
    
    try:
        value = await redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.error(f"Cache get failed for key {key}: {e}")
        return None


async def cache_delete(key: str) -> bool:
    """Delete value from cache"""
    if not redis_client:
        return False
    
    try:
        result = await redis_client.delete(key)
        return bool(result)
    except Exception as e:
        logger.error(f"Cache delete failed for key {key}: {e}")
        return False


def cache_key_builder(*args) -> str:
    """Build cache key from arguments"""
    return ":".join(str(arg) for arg in args)
