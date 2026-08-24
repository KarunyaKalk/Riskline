import time
from collections import defaultdict
from typing import Dict, List
from fastapi import Depends, HTTPException, Request, status

try:
    import redis
except ImportError:
    redis = None

from app.api.deps import get_current_user
from app.core.config import settings
from app.models.user import User

# In-memory fallback dictionary for test environments where Redis is not running
_in_memory_store: Dict[str, List[float]] = defaultdict(list)


class RateLimiter:
    """
    Per-user rate limiter backed by Redis with a fallback in-memory sliding window store.
    """

    def __init__(self, times: int = 60, seconds: int = 60):
        self.times = times
        self.seconds = seconds
        self.redis_client = None
        if redis and getattr(settings, "REDIS_URL", None):
            try:
                self.redis_client = redis.Redis.from_url(
                    settings.REDIS_URL, decode_responses=True, socket_connect_timeout=1
                )
            except Exception:
                self.redis_client = None

    def __call__(self, request: Request, current_user: User = Depends(get_current_user)) -> None:
        user_id_str = str(current_user.id)
        endpoint = request.url.path
        rate_key = f"rate_limit:{user_id_str}:{endpoint}"
        self._check_limit(rate_key)

    def _check_limit(self, rate_key: str) -> None:
        # 1. Attempt Redis rate limiting
        if self.redis_client:
            try:
                current_count = self.redis_client.incr(rate_key)
                if current_count == 1:
                    self.redis_client.expire(rate_key, self.seconds)
                if current_count > self.times:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded. Please try again later.",
                    )
                return
            except HTTPException:
                raise
            except Exception:
                pass

        # 2. In-memory sliding window fallback
        now = time.time()
        timestamps = _in_memory_store[rate_key]
        valid_timestamps = [t for t in timestamps if now - t < self.seconds]
        _in_memory_store[rate_key] = valid_timestamps

        if len(valid_timestamps) >= self.times:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )

        _in_memory_store[rate_key].append(now)


class AuthRateLimiter(RateLimiter):
    """
    IP-based rate limiter for unauthenticated auth endpoints (signup/login/password-reset).
    """

    def __call__(self, request: Request) -> None:
        client_ip = request.client.host if request.client else "127.0.0.1"
        endpoint = request.url.path
        rate_key = f"rate_limit_auth:{client_ip}:{endpoint}"
        self._check_limit(rate_key)


# Standard default rate limiters
rate_limit_mutations = RateLimiter(times=60, seconds=60)
rate_limit_auth = AuthRateLimiter(times=5, seconds=60)
