import redis.asyncio as aioredis
from .config import settings

# Redis bağlantı URL'si
REDIS_URL = f"redis://{settings.redis_hostname}:{settings.redis_port}"

# Global bir redis havuzu oluşturuyoruz
redis_client = aioredis.from_url(
    REDIS_URL, 
    encoding="utf-8", 
    decode_responses=True
)

async def get_redis():
    """Bağlantıyı test eder ve döner"""
    try:
        await redis_client.ping()
        return redis_client
    except Exception as e:
        print(f"Redis bağlantı hatası: {e}")
        raise e