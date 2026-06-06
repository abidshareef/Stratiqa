"""Custom middleware: lightweight rate limiting and security headers.

The rate limiter is an in-memory sliding window suitable for single-process
development. In production, back it with Redis (settings.redis_url) for a shared
window across workers.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, max_requests: int = 120, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        client = request.client.host if request.client else "anonymous"
        now = time.monotonic()
        bucket = self._hits[client]
        while bucket and now - bucket[0] > self.window:
            bucket.popleft()
        if len(bucket) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again shortly."},
            )
        bucket.append(now)
        return await call_next(request)
