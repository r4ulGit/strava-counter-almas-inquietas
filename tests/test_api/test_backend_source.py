"""Tests for api/backend_source.py — Lambda handler routing, auth, CORS."""
import os
import sys
import time
import hmac
import hashlib
import pytest
from unittest.mock import patch

API_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'api'))
WORKER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'worker'))

if WORKER_DIR in sys.path:
    sys.path.remove(WORKER_DIR)
if API_DIR in sys.path:
    sys.path.remove(API_DIR)
sys.path.insert(0, API_DIR)

SECRET = 'test-signing-secret-1234567890abcdef'
KEY = 'test-api-key'
ORIGIN = 'http://localhost:5173'


def make_sig(ts, nonce):
    return hmac.new(
        SECRET.encode('utf-8'),
        f"{ts}.{nonce}".encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


@pytest.fixture(autouse=True)
def api_env(monkeypatch):
    monkeypatch.setenv('API_KEY', KEY)
    monkeypatch.setenv('API_SIGNING_SECRET', SECRET)
    monkeypatch.setenv('AUTH_TOLERANCE_SECONDS', '300')
    monkeypatch.setenv('TOKEN_TTL_SECONDS', '300')
    monkeypatch.setenv('DYNAMODB_TABLE_NAME', 'ACTIVUM_ACT')
    monkeypatch.setenv('ATHLETES_TABLE_NAME', 'ACTIVUM_USR')
    monkeypatch.setenv('AWS_REGION', 'eu-west-1')
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'testing')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
    monkeypatch.setenv('GOAL_KM', '12000')
    monkeypatch.setenv('LAST_ACT', '5')
    monkeypatch.setenv('RATE_LIMIT_MAX', '100')
    monkeypatch.setenv('RATE_LIMIT_WINDOW', '60')
    monkeypatch.setenv('CORS_ALLOWED_ORIGINS', ORIGIN)


def make_event(method='GET', path='/', headers=None, source_ip='127.0.0.1'):
    h = {'origin': ORIGIN}
    if headers:
        h.update(headers)
    return {
        'httpMethod': method,
        'path': path,
        'headers': h,
        'requestContext': {'identity': {'sourceIp': source_ip}},
    }


def _load_modules():
    """Reload all api modules fresh with current env vars."""
    import importlib
    # Clear cached modules in dependency order
    for mod_name in ['api_config', 'auth', 'rate_limiter', 'utils', 'db', 'services', 'backend_source']:
        if mod_name in sys.modules:
            del sys.modules[mod_name]
    import api_config as cfg
    import auth
    import rate_limiter
    import utils
    import db
    import services
    import backend_source as bs
    return cfg, auth, bs


class TestOptionsPrelight:
    def test_options_returns_200(self):
        cfg, auth, bs = _load_modules()
        result = bs.process_activities(make_event('OPTIONS'), None)
        assert result['statusCode'] == 200

    def test_options_has_cors_headers(self):
        cfg, auth, bs = _load_modules()
        result = bs.process_activities(make_event('OPTIONS'), None)
        assert 'Access-Control-Allow-Origin' in result['headers']


class TestAuthTokenRoute:
    def test_valid_token_request_returns_200(self):
        cfg, auth, bs = _load_modules()
        ts = str(int(time.time()))
        nonce = 'abc123'
        sig = make_sig(ts, nonce)
        event = make_event('POST', '/auth/token', {
            'x-api-key': KEY,
            'x-timestamp': ts,
            'x-nonce': nonce,
            'x-signature': sig,
        })
        result = bs.process_activities(event, None)
        assert result['statusCode'] == 200

    def test_invalid_signature_returns_401(self):
        cfg, auth, bs = _load_modules()
        event = make_event('POST', '/auth/token', {
            'x-api-key': KEY,
            'x-timestamp': str(int(time.time())),
            'x-nonce': 'nonce',
            'x-signature': 'bad-sig',
        })
        result = bs.process_activities(event, None)
        assert result['statusCode'] == 401


class TestDataRoute:
    MOCK_DATA = {
        'total_km': 100.0, 'total_activities': 10,
        'top_athletes': [], 'last_activities': [],
        'config': {'goal_km': 12000}
    }

    def test_valid_bearer_token_returns_200(self):
        cfg, auth_mod, bs = _load_modules()
        token, _ = auth_mod.generate_token()
        event = make_event('GET', '/', {'authorization': f'Bearer {token}'})
        with patch.object(bs.services, 'build_dashboard_data', return_value=self.MOCK_DATA):
            result = bs.process_activities(event, None)
        assert result['statusCode'] == 200

    def test_no_token_returns_401(self):
        cfg, auth_mod, bs = _load_modules()
        result = bs.process_activities(make_event('GET', '/'), None)
        assert result['statusCode'] == 401

    def test_passthrough_mode_no_auth_needed(self, monkeypatch):
        monkeypatch.setenv('API_KEY', '')
        monkeypatch.setenv('API_SIGNING_SECRET', '')
        cfg, auth_mod, bs = _load_modules()
        with patch.object(bs.services, 'build_dashboard_data', return_value={
            'total_km': 50.0, 'total_activities': 5,
            'top_athletes': [], 'last_activities': [],
            'config': {'goal_km': 500}
        }):
            result = bs.process_activities(make_event('GET', '/'), None)
        assert result['statusCode'] == 200

    def test_cors_headers_present_on_data_response(self):
        cfg, auth_mod, bs = _load_modules()
        token, _ = auth_mod.generate_token()
        event = make_event('GET', '/', {'authorization': f'Bearer {token}'})
        with patch.object(bs.services, 'build_dashboard_data', return_value=self.MOCK_DATA):
            result = bs.process_activities(event, None)
        assert 'Access-Control-Allow-Origin' in result['headers']


class TestUnknownRoute:
    def test_unknown_path_returns_404(self):
        cfg, auth_mod, bs = _load_modules()
        result = bs.process_activities(make_event('GET', '/unknown'), None)
        assert result['statusCode'] == 404
