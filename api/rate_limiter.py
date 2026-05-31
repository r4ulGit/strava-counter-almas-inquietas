import time
import api_config as config

# In-memory sliding window request history per IP.
# NOTE: Resets on Lambda cold starts.
_request_history: dict[str, list[float]] = {}


def is_rate_limited(client_ip: str) -> bool:
    """
    Checks whether a client IP has exceeded the rate limit.
    Uses a sliding window algorithm.

    Args:
        client_ip: The client's IP address string.

    Returns:
        True if the client is rate limited (request should be blocked).
        False if the request is within limits (request is allowed and recorded).
    """
    now = time.time()
    window_start = now - config.RATE_LIMIT_WINDOW

    history = _request_history.get(client_ip, [])
    # Discard timestamps outside the current window
    history = [t for t in history if t > window_start]

    if len(history) >= config.RATE_LIMIT_MAX:
        return True

    history.append(now)
    _request_history[client_ip] = history
    return False
