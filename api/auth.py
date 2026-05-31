import hmac
import hashlib
import time
import uuid
import api_config as config

# In-memory token store.
# NOTE: This resets on Lambda cold starts, which is acceptable for single-user use.
_active_tokens: dict[str, float] = {}


def is_auth_enabled() -> bool:
    """Returns True if auth is configured (both API_KEY and API_SIGNING_SECRET are set)."""
    return bool(config.API_KEY and config.API_SIGNING_SECRET)


def verify_signature(api_key: str, timestamp: str, nonce: str, signature: str) -> bool:
    """
    Validates an incoming HMAC-SHA256 auth request.

    Checks:
    1. api_key matches the configured API_KEY
    2. timestamp is within AUTH_TOLERANCE_SECONDS of server time
    3. HMAC-SHA256(API_SIGNING_SECRET, "{timestamp}.{nonce}") matches the provided signature
    """
    if api_key != config.API_KEY:
        return False

    try:
        ts = float(timestamp)
    except (ValueError, TypeError):
        return False

    if abs(time.time() - ts) > config.AUTH_TOLERANCE_SECONDS:
        return False

    expected = hmac.new(
        config.API_SIGNING_SECRET.encode('utf-8'),
        f"{timestamp}.{nonce}".encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


def generate_token() -> tuple[str, int]:
    """
    Generates a new short-lived bearer token and stores it in the in-memory cache.

    Returns:
        (token, ttl_seconds)
    """
    _cleanup_expired()
    token = str(uuid.uuid4())
    _active_tokens[token] = time.time() + config.TOKEN_TTL_SECONDS
    return token, config.TOKEN_TTL_SECONDS


def verify_token(token: str) -> bool:
    """
    Checks whether a bearer token is valid and not expired.
    """
    _cleanup_expired()
    return token in _active_tokens


def _cleanup_expired():
    """Lazily removes expired tokens from the in-memory store."""
    now = time.time()
    expired = [k for k, exp in _active_tokens.items() if exp < now]
    for k in expired:
        del _active_tokens[k]
