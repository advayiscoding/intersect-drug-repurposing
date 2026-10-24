"""Per-session token bucket for live checks.

Live checks spend both the PubMed quota and the LLM budget, so a session gets a
small fixed allowance. In-memory and per process: this is a brake on repeated
clicking in a local demo, not an authentication boundary.
"""
from __future__ import annotations

import threading
import time

LIMIT = 5
WINDOW_SECONDS = 600


class RateLimiter:
    def __init__(self, limit: int = LIMIT, window: float = WINDOW_SECONDS):
        self.limit, self.window = limit, window
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def check(self, session: str, now: float | None = None) -> dict:
        """Consume one token. Returns allowed plus what is left and when it resets."""
        now = time.monotonic() if now is None else now
        with self._lock:
            recent = [t for t in self._hits.get(session, []) if now - t < self.window]
            if len(recent) >= self.limit:
                self._hits[session] = recent
                return {"allowed": False, "remaining": 0,
                        "retry_after_seconds": round(self.window - (now - recent[0]), 1),
                        "limit": self.limit, "window_seconds": self.window}
            recent.append(now)
            self._hits[session] = recent
            return {"allowed": True, "remaining": self.limit - len(recent),
                    "retry_after_seconds": 0, "limit": self.limit, "window_seconds": self.window}


limiter = RateLimiter()
