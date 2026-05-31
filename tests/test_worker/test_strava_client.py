"""Tests for worker/strava_client.py — auth and activity fetching."""
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

WORKER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'worker'))
if WORKER_DIR not in sys.path:
    sys.path.insert(0, WORKER_DIR)


@pytest.fixture(autouse=True)
def worker_env(monkeypatch):
    monkeypatch.setenv('STRAVA_CLIENT_ID', '12345')
    monkeypatch.setenv('STRAVA_CLIENT_SECRET', 'secret')
    monkeypatch.setenv('STRAVA_REFRESH_TOKEN', 'refresh-token')
    monkeypatch.setenv('STRAVA_CLUB_IDS', '["1793883"]')
    monkeypatch.setenv('ACTIVITIES_TABLE_NAME', 'ACTIVUM_ACT')
    monkeypatch.setenv('ATHLETES_TABLE_NAME', 'ACTIVUM_USR')
    monkeypatch.setenv('AWS_REGION', 'eu-west-1')


class TestRefreshAccessToken:
    def test_returns_access_token_on_success(self, monkeypatch):
        import importlib, config as cfg
        import strava_client as sc
        importlib.reload(cfg)
        importlib.reload(sc)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'access_token': 'new-token-abc'}
        mock_resp.raise_for_status = MagicMock()

        with patch('requests.post', return_value=mock_resp) as mock_post:
            token = sc.refresh_access_token()

        assert token == 'new-token-abc'
        mock_post.assert_called_once()

    def test_returns_none_on_auth_failure(self, monkeypatch):
        import importlib, config as cfg
        import strava_client as sc
        importlib.reload(cfg)
        importlib.reload(sc)

        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("401 Unauthorized")

        with patch('requests.post', return_value=mock_resp):
            token = sc.refresh_access_token()

        assert token is None


class TestGetClubActivities:
    def test_returns_activities_on_success(self, monkeypatch):
        import importlib, config as cfg
        import strava_client as sc
        importlib.reload(cfg)
        importlib.reload(sc)

        page1 = [{'name': 'Run 1', 'distance': 5000}] * 5
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = page1

        with patch('requests.get', return_value=mock_resp):
            activities = sc.get_club_activities('token-abc', '1793883')

        assert len(activities) == 5

    def test_returns_empty_list_on_api_error(self, monkeypatch):
        import importlib, config as cfg
        import strava_client as sc
        importlib.reload(cfg)
        importlib.reload(sc)

        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("403 Forbidden")

        with patch('requests.get', return_value=mock_resp):
            activities = sc.get_club_activities('bad-token', '9999')

        assert activities == []

    def test_uses_correct_club_url(self, monkeypatch):
        import importlib, config as cfg
        import strava_client as sc
        importlib.reload(cfg)
        importlib.reload(sc)

        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = []  # Empty — stops pagination

        with patch('requests.get', return_value=mock_resp) as mock_get:
            sc.get_club_activities('token', '1793883')

        called_url = mock_get.call_args[0][0]
        assert '1793883' in called_url
        assert 'clubs' in called_url
