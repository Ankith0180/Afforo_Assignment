import time
import redis
from redis.exceptions import ConnectionError as RedisConnectionError, TimeoutError as RedisTimeoutError
from django.conf import settings
from rest_framework.throttling import BaseThrottle

# Redis client (lazy connect)
r = redis.Redis.from_url(settings.REDIS_URL)


class SuggestRateThrottle(BaseThrottle):
    """
    Throttle: max 20 requests per minute per IP.

    IMPORTANT:
    - If Redis is down / not reachable, we DO NOT break the request.
      We just skip throttling and allow the request (graceful fallback).
    """
    rate = 20  # requests per minute

    def get_ident(self, request):
        # identify client by IP (simplest)
        return request.META.get("REMOTE_ADDR", "anonymous")

    def allow_request(self, request, view):
        ident = self.get_ident(request)
        key = f"suggest:{ident}"
        now = int(time.time())

        try:
            with r.pipeline() as pipe:
                # 1) Remove timestamps older than 60 seconds
                pipe.zremrangebyscore(key, 0, now - 60)
                # 2) Add current timestamp
                pipe.zadd(key, {str(now): now})
                # 3) Count entries in last 60s
                pipe.zcard(key)
                # 4) Keep key alive
                pipe.expire(key, 60)
                results = pipe.execute()

            # results = [None, None, count, True/False]
            count = results[2]

            return count <= self.rate

        except (RedisConnectionError, RedisTimeoutError, OSError):
            # Redis is not running / not reachable:
            # -> fail OPEN (no throttling) instead of 500
            return True

    def wait(self):
        # how long client should wait when throttled (DRF uses this)
        return 60
