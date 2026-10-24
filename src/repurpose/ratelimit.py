"""Per-session token bucket for live checks.

Live checks spend both the PubMed quota and the LLM budget, so a session gets a
small fixed allowance. In-memory and per process: this is a brake on repeated
clicking in a local demo, not an authentication boundary.
"""
from __future__ import annotations

import threading
import time
import json
import os
import tempfile
import fcntl
from datetime import date

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

DEFAULT_DAILY_CAP = 40


class DailyCap:
    """Process-wide cap on live agent runs, persisted so a restart cannot reset it.

    The per-session limiter stops one impatient visitor; this stops the whole demo
    from spending more than a day's budget however many sessions arrive.
    """

    def __init__(self, path, limit: int | None = None):
        self.path = path
        self.limit = limit if limit is not None else DEFAULT_DAILY_CAP

    def _read(self, day: str) -> int:
        try:
            state = json.loads(self.path.read_text())
            count = state["count"]
            if type(count) is not int or count < 0 or not isinstance(state["day"], str):
                raise ValueError("Invalid budget counter")
            saved_day = date.fromisoformat(state["day"])
            if saved_day.isoformat() != state["day"] or saved_day > date.fromisoformat(day):
                raise ValueError("Invalid or future budget day")
            return count if state["day"] == day else 0
        except FileNotFoundError:
            return 0
        except (OSError, ValueError, KeyError, TypeError):
            # A damaged counter must never grant a fresh budget.
            return self.limit

    def state(self, today: str | None = None) -> dict:
        day = today or time.strftime("%Y-%m-%d", time.gmtime())
        used = self._read(day)
        return {"day": day, "limit": self.limit, "used": used,
                "remaining": max(0, self.limit - used)}

    def check(self, today: str | None = None) -> dict:
        """Consume one run from today's budget."""
        day = today or time.strftime("%Y-%m-%d", time.gmtime())
        # Separate lock file survives atomic replacement and synchronizes both
        # threads and worker processes on the same POSIX disk (macOS/Linux).
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.with_suffix(".lock").open("a") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                used = self._read(day)
                if used >= self.limit:
                    return {"allowed": False, **self.state(day)}
                with tempfile.NamedTemporaryFile(mode="w", dir=self.path.parent,
                                                 prefix="live-runs-", delete=False) as stream:
                    json.dump({"day": day, "count": used + 1}, stream)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(stream.name, self.path)
                return {"allowed": True, **self.state(day)}
        except OSError:
            return {"allowed": False, **self.state(day), "storage_error": True}


def daily_cap(root) -> DailyCap:
    import os
    limit = os.environ.get("REPURPOSE_DAILY_LIVE_CAP")
    return DailyCap(root / "data/cache/live_runs.json",
                    int(limit) if limit and limit.isdigit() else None)
