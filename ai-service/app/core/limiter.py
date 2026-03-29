import time
from collections import defaultdict
from typing import Dict, List

# ip -> list of timestamps
_request_history: Dict[str, List[float]] = defaultdict(list)

def is_rate_limited(ip: str, limit: int = 60, window: int = 60) -> bool:
    """
    Check if an IP is rate limited.
    limit: max requests in window
    window: time window in seconds
    """
    now = time.time()
    
    # Clean up old timestamps
    _request_history[ip] = [ts for ts in _request_history[ip] if now - ts < window]
    
    if len(_request_history[ip]) >= limit:
        return True
    
    # Record current request
    _request_history[ip].append(now)
    return False
