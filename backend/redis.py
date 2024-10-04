# import aioredis
# from django.conf import settings

# redis_pool = None

# async def get_redis_pool():
#     global redis_pool
#     if redis_pool is None:
#         redis_pool = await aioredis.create_redis_pool(settings.REDIS_URL)
#     return redis_pool


