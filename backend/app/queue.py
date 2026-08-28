import os

from redis import Redis
from rq import Queue


REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://redis:6379/0",
)

redis_connection = Redis.from_url(
    REDIS_URL,
    decode_responses=True,
)

publish_queue = Queue(
    "publish",
    connection=redis_connection,
)

reel_queue = Queue(
    "reel",
    connection=redis_connection,
)