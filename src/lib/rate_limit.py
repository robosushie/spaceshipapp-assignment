import time
from collections import defaultdict


class LoginRateLimiter:
    """Five login attempts per 60 seconds, per client address, in this process."""

    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = defaultdict(list)

    def retry_after(self, key: str) -> int | None:
        now = time.monotonic()
        recent = [stamp for stamp in self._hits[key] if now - stamp < 60]
        if len(recent) >= 5:
            self._hits[key] = recent
            return max(1, int(60 - (now - recent[0])) + 1)
        recent.append(now)
        self._hits[key] = recent
        return None

    def reset(self) -> None:
        self._hits.clear()


login_limiter = LoginRateLimiter()
