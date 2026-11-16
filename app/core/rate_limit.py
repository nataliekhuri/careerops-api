"""A small in-memory sliding-window rate limiter.

Render's free plan runs a **single instance** (see README "Deployment"), so counting
attempts in process memory is correct here and needs no extra paid service (such as
Redis). If the API is ever scaled to more than one instance, replace the in-memory
store with a shared one; the call sites in `app/api/rate_limit.py` would not change.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock

from fastapi import HTTPException, status


@dataclass
class RateLimiter:
    """Allows at most `limit` hits per key within a sliding window of `window` seconds."""

    limit: int
    window: float
    _hits: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list), repr=False)
    _lock: Lock = field(default_factory=Lock, repr=False)

    def hit(self, key: str) -> None:
        """Record one attempt for `key`. Raises 429 (with `Retry-After`) once the limit is passed."""
        now = time.monotonic()
        with self._lock:
            recent = [t for t in self._hits[key] if now - t < self.window]
            recent.append(now)
            self._hits[key] = recent
            if len(recent) > self.limit:
                retry_after = max(1, int(self.window - (now - recent[0])) + 1)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many attempts. Please try again later.",
                    headers={"Retry-After": str(retry_after)},
                )

    def reset(self) -> None:
        """Clear every recorded attempt (used by tests)."""
        with self._lock:
            self._hits.clear()
