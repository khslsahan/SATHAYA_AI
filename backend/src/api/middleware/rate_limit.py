"""Rate limiting middleware."""

import time
from collections import defaultdict
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import get_settings

settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""

    def __init__(self, app, requests_per_minute: int = None, requests_per_hour: int = None):
        """Initialize rate limiter."""
        super().__init__(app)
        self.requests_per_minute = requests_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self.requests_per_hour = requests_per_hour or settings.RATE_LIMIT_PER_HOUR
        self.minute_requests = defaultdict(list)
        self.hour_requests = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        """Check rate limits before processing request."""
        # Get client identifier
        client_id = request.client.host if request.client else "unknown"

        # Check minute limit
        current_time = time.time()
        self.minute_requests[client_id] = [
            t for t in self.minute_requests[client_id]
            if current_time - t < 60
        ]

        if len(self.minute_requests[client_id]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )

        # Check hour limit
        self.hour_requests[client_id] = [
            t for t in self.hour_requests[client_id]
            if current_time - t < 3600
        ]

        if len(self.hour_requests[client_id]) >= self.requests_per_hour:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Hourly rate limit exceeded. Please try again later.",
            )

        # Record request
        self.minute_requests[client_id].append(current_time)
        self.hour_requests[client_id].append(current_time)

        # Process request
        response = await call_next(request)
        return response

