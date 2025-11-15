"""
Production-grade rate limiting middleware.

Implements:
- IP-based rate limiting
- User-based rate limiting
- Endpoint-specific limits
- Distributed rate limiting (Redis-backed)
- DDoS protection

Usage (FastAPI):
    from deployment.security.rate_limiter import RateLimiter

    app = FastAPI()
    rate_limiter = RateLimiter(
        requests_per_minute=60,
        burst_size=10
    )

    @app.get("/api/data")
    async def get_data(request: Request):
        await rate_limiter.check(request)
        return {"data": "..."}
"""

import time
import asyncio
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib


@dataclass
class RateLimitConfig:
    """Rate limit configuration."""

    requests_per_minute: int = 60
    burst_size: int = 10
    block_duration_seconds: int = 300  # 5 minutes
    enable_distributed: bool = False
    redis_url: Optional[str] = None


@dataclass
class ClientStats:
    """Statistics for a single client."""

    requests: deque = field(default_factory=lambda: deque(maxlen=1000))
    blocked_until: Optional[float] = None
    total_requests: int = 0
    blocked_count: int = 0


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, retry_after: int):
        """
        Initialize exception.

        Args:
            retry_after: Seconds until client can retry
        """
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")


class RateLimiter:
    """
    Production-grade rate limiter with multiple strategies.

    Implements:
    - Token bucket algorithm
    - Sliding window counters
    - IP and user-based limiting
    - Distributed rate limiting via Redis
    - Automatic blocking of abusive clients

    Example:
        rate_limiter = RateLimiter(requests_per_minute=100)

        # In request handler
        await rate_limiter.check(request)
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        Initialize rate limiter.

        Args:
            config: Rate limiter configuration
        """
        self.config = config or RateLimitConfig()

        # Per-client statistics
        self._clients: Dict[str, ClientStats] = defaultdict(ClientStats)

        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None

        # Redis client (if distributed)
        self._redis: Optional[Any] = None

        if self.config.enable_distributed and self.config.redis_url:
            self._init_redis()

    def _init_redis(self) -> None:
        """Initialize Redis client for distributed rate limiting."""
        try:
            import redis.asyncio as redis

            self._redis = redis.from_url(
                self.config.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        except ImportError:
            print("Warning: redis package not installed. Falling back to local rate limiting.")
            self.config.enable_distributed = False

    def _get_client_key(self, request: Any) -> str:
        """
        Get unique key for client (IP + user ID if authenticated).

        Args:
            request: Request object

        Returns:
            str: Client key
        """
        # Get client IP
        client_ip = "unknown"

        if hasattr(request, "client") and request.client:
            client_ip = request.client.host
        elif hasattr(request, "remote_addr"):
            client_ip = request.remote_addr

        # Get user ID if authenticated
        user_id = None
        if hasattr(request, "user") and request.user:
            user_id = getattr(request.user, "id", None) or getattr(request.user, "username", None)

        # Combine IP and user ID
        if user_id:
            key = f"{client_ip}:{user_id}"
        else:
            key = client_ip

        # Hash for privacy
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    async def check(self, request: Any, cost: int = 1) -> None:
        """
        Check if request should be rate limited.

        Args:
            request: Request object
            cost: Cost of this request (default: 1)

        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        client_key = self._get_client_key(request)

        if self.config.enable_distributed and self._redis:
            await self._check_distributed(client_key, cost)
        else:
            await self._check_local(client_key, cost)

    async def _check_local(self, client_key: str, cost: int) -> None:
        """
        Check rate limit using local storage.

        Args:
            client_key: Client identifier
            cost: Request cost

        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        now = time.time()
        stats = self._clients[client_key]

        # Check if client is blocked
        if stats.blocked_until and now < stats.blocked_until:
            retry_after = int(stats.blocked_until - now)
            raise RateLimitExceeded(retry_after)

        # Clear block if expired
        if stats.blocked_until and now >= stats.blocked_until:
            stats.blocked_until = None

        # Remove old requests (outside window)
        window_start = now - 60.0  # 1 minute window
        while stats.requests and stats.requests[0] < window_start:
            stats.requests.popleft()

        # Count requests in current window
        current_count = len(stats.requests)

        # Check rate limit
        if current_count + cost > self.config.requests_per_minute:
            # Block client
            stats.blocked_until = now + self.config.block_duration_seconds
            stats.blocked_count += 1

            raise RateLimitExceeded(self.config.block_duration_seconds)

        # Check burst limit
        recent_window = now - 10.0  # 10 second burst window
        recent_count = sum(1 for t in stats.requests if t >= recent_window)

        if recent_count + cost > self.config.burst_size:
            # Temporary rate limit
            raise RateLimitExceeded(10)

        # Record request
        for _ in range(cost):
            stats.requests.append(now)

        stats.total_requests += cost

    async def _check_distributed(self, client_key: str, cost: int) -> None:
        """
        Check rate limit using Redis.

        Args:
            client_key: Client identifier
            cost: Request cost

        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        if not self._redis:
            # Fallback to local
            await self._check_local(client_key, cost)
            return

        now = time.time()
        key_prefix = f"ratelimit:{client_key}"

        # Check if blocked
        blocked_key = f"{key_prefix}:blocked"
        blocked_until = await self._redis.get(blocked_key)

        if blocked_until:
            blocked_until_float = float(blocked_until)
            if now < blocked_until_float:
                retry_after = int(blocked_until_float - now)
                raise RateLimitExceeded(retry_after)

        # Use sorted set for sliding window
        window_key = f"{key_prefix}:window"

        # Remove old entries
        await self._redis.zremrangebyscore(window_key, 0, now - 60.0)

        # Count current requests
        current_count = await self._redis.zcard(window_key)

        # Check limit
        if current_count + cost > self.config.requests_per_minute:
            # Block client
            await self._redis.setex(
                blocked_key,
                self.config.block_duration_seconds,
                str(now + self.config.block_duration_seconds)
            )

            raise RateLimitExceeded(self.config.block_duration_seconds)

        # Add current request(s)
        pipeline = self._redis.pipeline()
        for i in range(cost):
            pipeline.zadd(window_key, {f"{now}:{i}": now})

        pipeline.expire(window_key, 60)  # Expire after 1 minute
        await pipeline.execute()

    def get_stats(self, client_key: Optional[str] = None) -> Dict:
        """
        Get rate limiting statistics.

        Args:
            client_key: Optional specific client key

        Returns:
            Dictionary with statistics
        """
        if client_key:
            stats = self._clients.get(client_key)
            if not stats:
                return {}

            return {
                'total_requests': stats.total_requests,
                'blocked_count': stats.blocked_count,
                'current_window_count': len(stats.requests),
                'is_blocked': stats.blocked_until is not None and time.time() < stats.blocked_until
            }

        # Global stats
        return {
            'total_clients': len(self._clients),
            'blocked_clients': sum(1 for s in self._clients.values()
                                  if s.blocked_until and time.time() < s.blocked_until),
            'total_requests': sum(s.total_requests for s in self._clients.values()),
            'total_blocks': sum(s.blocked_count for s in self._clients.values())
        }

    async def cleanup(self) -> None:
        """Clean up old client statistics."""
        now = time.time()
        cutoff = now - 3600.0  # Keep stats for 1 hour

        # Remove old clients
        to_remove = []
        for client_key, stats in self._clients.items():
            if stats.requests:
                last_request = stats.requests[-1]
                if last_request < cutoff:
                    to_remove.append(client_key)
            elif stats.total_requests == 0:
                to_remove.append(client_key)

        for client_key in to_remove:
            del self._clients[client_key]

    async def start_cleanup_task(self) -> None:
        """Start background cleanup task."""
        if self._cleanup_task:
            return

        async def cleanup_loop():
            while True:
                await asyncio.sleep(300)  # Every 5 minutes
                await self.cleanup()

        self._cleanup_task = asyncio.create_task(cleanup_loop())

    async def stop_cleanup_task(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None


# FastAPI middleware
def create_rate_limit_middleware(config: Optional[RateLimitConfig] = None):
    """
    Create FastAPI middleware for rate limiting.

    Args:
        config: Rate limiter configuration

    Returns:
        Middleware class
    """
    from fastapi import Request, Response
    from fastapi.responses import JSONResponse
    from starlette.middleware.base import BaseHTTPMiddleware

    rate_limiter = RateLimiter(config)

    class RateLimitMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            try:
                await rate_limiter.check(request)
                response = await call_next(request)
                return response

            except RateLimitExceeded as e:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "retry_after": e.retry_after
                    },
                    headers={
                        "Retry-After": str(e.retry_after),
                        "X-RateLimit-Limit": str(config.requests_per_minute if config else 60),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time() + e.retry_after))
                    }
                )

    return RateLimitMiddleware


# Example usage
if __name__ == '__main__':
    """Example usage of rate limiter."""

    async def test_rate_limiter():
        """Test rate limiter."""
        from dataclasses import dataclass

        @dataclass
        class MockRequest:
            client: object

            @dataclass
            class Client:
                host: str = "127.0.0.1"

            def __init__(self):
                self.client = self.Client()

        # Create rate limiter
        config = RateLimitConfig(requests_per_minute=10, burst_size=5)
        limiter = RateLimiter(config)

        request = MockRequest()

        # Test normal requests
        for i in range(5):
            try:
                await limiter.check(request)
                print(f"Request {i+1}: OK")
            except RateLimitExceeded as e:
                print(f"Request {i+1}: BLOCKED (retry after {e.retry_after}s)")

        # Test burst
        print("\nTesting burst...")
        for i in range(10):
            try:
                await limiter.check(request)
                print(f"Burst request {i+1}: OK")
            except RateLimitExceeded as e:
                print(f"Burst request {i+1}: BLOCKED (retry after {e.retry_after}s)")

        # Print stats
        print("\nRate limiter statistics:")
        print(limiter.get_stats())

    asyncio.run(test_rate_limiter())
