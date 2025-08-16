import time
import os
from collections import deque
from threading import Lock

# Requests-per-minute per token (configurable via env)
RPM = int(os.environ.get("RATE_LIMIT_RPM", "60"))
WINDOW = 60.0  # seconds

_queues: dict[str, deque] = {}
_lock = Lock()

def rate_limit(token: str) -> bool:
    """
    Return True if the request is allowed for this token, False if rate-limited.
    Sliding window over the last 60 seconds, per token.
    """
    now = time.time()
    with _lock:
        dq = _queues.setdefault(token, deque())
        # drop timestamps older than WINDOW
        while dq and (now - dq[0]) > WINDOW:
            dq.popleft()
        if len(dq) >= RPM:
            return False
        dq.append(now)
        return True
