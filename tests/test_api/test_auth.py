"""Tests for api/auth.py — HMAC verification, token lifecycle, passthrough mode."""
import os
import sys
import time
import hmac
import hashlib
import pytest

API_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'api'))
WORKER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'worker'))

if WORKER_DIR in sys.path:
    sys.path.remove(WORKER_DIR)
if API_DIR in sys.path:
    sys.path.remove(API_DIR)
sys.path.insert(0, API_DIR)

SECRET = 'test-signing-secret-1234567890abcdef'
KEY = 'test-api-key'


def make_valid_signature(secret, timestamp, nonce):
    return hmac.new(
        secret.encode('utf-8'),
        f"{timestamp}.{nonce}".encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def _reload():
    """Reload config and auth fresh from current environment."""
    for mod_name in ['api_config', 'auth']:
        if mod_name in sys.modules:
            del sys.modules[mod_name]
    import api_config as cfg
    import auth
    return cfg, auth


@pytest.fixture(autouse=True)
def api_env(monkeypatch):
    monkeypatch.setenv('API_KEY', KEY)
    monkeypatch.setenv('API_SIGNING_SECRET', SECRET)
    monkeypatch.setenv('AUTH_TOLERANCE_SECONDS', '300')
    monkeypatch.setenv('TOKEN_TTL_SECONDS', '10')
    monkeypatch.setenv('DYNAMODB_TABLE_NAME', 'ACTIVUM_ACT')
    monkeypatch.setenv('ATHLETES_TABLE_NAME', 'ACTIVUM_USR')
    monkeypatch.setenv('AWS_REGION', 'eu-west-1')
    monkeypatch.setenv('GOAL_KM', '12000')
    monkeypatch.setenv('LAST_ACT', '5')
    monkeypatch.setenv('RATE_LIMIT_MAX', '10')
    monkeypatch.setenv('RATE_LIMIT_WINDOW', '60')
    monkeypatch.setenv('CORS_ALLOWED_ORIGINS', 'http://localhost:5173')


class TestIsAuthEnabled:
    def test_enabled_when_both_keys_set(self):
        cfg, auth = _reload()
        assert auth.is_auth_enabled() is True

    def test_disabled_when_api_key_empty(self, monkeypatch):
        monkeypatch.setenv('API_KEY', '')
        cfg, auth = _reload()
        assert auth.is_auth_enabled() is False

    def test_disabled_when_secret_empty(self, monkeypatch):
        monkeypatch.setenv('API_SIGNING_SECRET', '')
        cfg, auth = _reload()
        assert auth.is_auth_enabled() is False


class TestVerifySignature:
    def test_valid_signature_returns_true(self):
        cfg, auth = _reload()
        ts = str(int(time.time()))
        nonce = 'abc123'
        sig = make_valid_signature(SECRET, ts, nonce)
        assert auth.verify_signature(KEY, ts, nonce, sig) is True

    def test_wrong_api_key_returns_false(self):
        cfg, auth = _reload()
        ts = str(int(time.time()))
        nonce = 'abc123'
        sig = make_valid_signature(SECRET, ts, nonce)
        assert auth.verify_signature('wrong-key', ts, nonce, sig) is False

    def test_wrong_signature_returns_false(self):
        cfg, auth = _reload()
        ts = str(int(time.time()))
        assert auth.verify_signature(KEY, ts, 'nonce', 'bad-signature') is False

    def test_expired_timestamp_returns_false(self, monkeypatch):
        monkeypatch.setenv('AUTH_TOLERANCE_SECONDS', '5')
        cfg, auth = _reload()
        old_ts = str(int(time.time()) - 300)  # 5 minutes ago
        nonce = 'abc123'
        sig = make_valid_signature(SECRET, old_ts, nonce)
        assert auth.verify_signature(KEY, old_ts, nonce, sig) is False

    def test_non_numeric_timestamp_returns_false(self):
        cfg, auth = _reload()
        assert auth.verify_signature(KEY, 'not-a-number', 'nonce', 'sig') is False


class TestTokenLifecycle:
    def test_generate_token_returns_token_and_ttl(self):
        cfg, auth = _reload()
        token, ttl = auth.generate_token()
        assert isinstance(token, str)
        assert len(token) > 10
        assert ttl == 10  # TOKEN_TTL_SECONDS=10 in fixture

    def test_valid_token_is_accepted(self):
        cfg, auth = _reload()
        token, _ = auth.generate_token()
        assert auth.verify_token(token) is True

    def test_invalid_token_is_rejected(self):
        cfg, auth = _reload()
        assert auth.verify_token('fake-token-xyz') is False

    def test_expired_token_is_rejected(self, monkeypatch):
        monkeypatch.setenv('TOKEN_TTL_SECONDS', '1')
        cfg, auth = _reload()
        token, _ = auth.generate_token()
        # Manually expire the token by backdating it
        auth._active_tokens[token] = time.time() - 1
        assert auth.verify_token(token) is False
