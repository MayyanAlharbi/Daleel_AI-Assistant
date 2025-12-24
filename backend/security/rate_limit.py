# backend/security/rate_limit.py
import time
from collections import defaultdict, deque

# 30 requests per minute per IP per route
DEFAULT_LIMIT = 30
WINDOW_SECONDS = 60

class RateLimiter:
    def __init__(self):
        self.buckets = defaultdict(deque)

    def check(self, key: str, limit: int = DEFAULT_LIMIT) -> None:
        now = time.time()
        q = self.buckets[key]

        # drop old timestamps
        while q and (now - q[0]) > WINDOW_SECONDS:
            q.popleft()

        if len(q) >= limit:
            raise ValueError("Rate limit exceeded. Please slow down.")

        q.append(now)

limiter = RateLimiter()
