"""Tests for api/rate_limiter.py — sliding window rate limiting."""
import os
import sys
import time
import pytest

API_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'api'))
WORKER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'worker'))

if WORKER_DIR in sys.path:
    sys.path.remove(WORKER_DIR)
if API_DIR in sys.path:
    sys.path.remove(API_DIR)
sys.path.insert(0, API_DIR)


@pytest.fixture(autouse=True)
def api_env(monkeypatch):
    monkeypatch.setenv('RATE_LIMIT_MAX', '3')
    monkeypatch.setenv('RATE_LIMIT_WINDOW', '60')
    monkeypatch.setenv('API_KEY', 'key')
    monkeypatch.setenv('API_SIGNING_SECRET', 'secret')
    monkeypatch.setenv('DYNAMODB_TABLE_NAME', 'ACTIVUM_ACT')
    monkeypatch.setenv('ATHLETES_TABLE_NAME', 'ACTIVUM_USR')
    monkeypatch.setenv('AWS_REGION', 'eu-west-1')
    monkeypatch.setenv('GOAL_KM', '500')
    monkeypatch.setenv('LAST_ACT', '5')
    monkeypatch.setenv('CORS_ALLOWED_ORIGINS', 'http://localhost:5173')
    monkeypatch.setenv('AUTH_TOLERANCE_SECONDS', '300')
    monkeypatch.setenv('TOKEN_TTL_SECONDS', '300')


def _get_fresh_limiter():
    """Reload config + rate_limiter and clear the in-memory history."""
    for mod_name in ['api_config', 'rate_limiter']:
        if mod_name in sys.modules:
            del sys.modules[mod_name]
    import api_config  # noqa: F401
    import rate_limiter as rl
    rl._request_history.clear()
    return rl


class TestRateLimiter:
    def test_first_request_is_allowed(self):
        rl = _get_fresh_limiter()
        assert rl.is_rate_limited('10.0.0.1') is False

    def test_requests_within_limit_are_allowed(self):
        rl = _get_fresh_limiter()
        # RATE_LIMIT_MAX = 3
        assert rl.is_rate_limited('10.0.0.2') is False
        assert rl.is_rate_limited('10.0.0.2') is False
        assert rl.is_rate_limited('10.0.0.2') is False

    def test_request_exceeding_limit_is_blocked(self):
        rl = _get_fresh_limiter()
        rl.is_rate_limited('10.0.0.3')
        rl.is_rate_limited('10.0.0.3')
        rl.is_rate_limited('10.0.0.3')
        # 4th request — should be blocked
        assert rl.is_rate_limited('10.0.0.3') is True

    def test_different_ips_are_independent(self):
        rl = _get_fresh_limiter()
        for _ in range(3):
            rl.is_rate_limited('192.168.1.1')
        # Maxed out for 192.168.1.1 but not for 192.168.1.2
        assert rl.is_rate_limited('192.168.1.1') is True
        assert rl.is_rate_limited('192.168.1.2') is False

    def test_old_requests_outside_window_dont_count(self):
        rl = _get_fresh_limiter()
        ip = '10.0.0.4'
        # Inject old timestamps outside the 60s window
        old_time = time.time() - 120
        rl._request_history[ip] = [old_time, old_time, old_time]
        # Should NOT be rate limited since old requests are outside the window
        assert rl.is_rate_limited(ip) is False
