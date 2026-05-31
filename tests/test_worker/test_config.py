"""Tests for worker/config.py — environment variable loading."""
import importlib
import json
import sys
import os
import pytest
from unittest.mock import patch

# Ensure worker dir is on path
WORKER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'worker'))
if WORKER_DIR not in sys.path:
    sys.path.insert(0, WORKER_DIR)


def reload_config(monkeypatch):
    """
    Force reload of the worker config module.
    We patch load_dotenv to a no-op so the .env file on disk doesn't override
    the monkeypatched environment variables.
    """
    for mod in ['config']:
        if mod in sys.modules:
            del sys.modules[mod]

    with patch('dotenv.load_dotenv'):
        import config
        return config


class TestStravaClubIds:
    def test_parse_valid_json_array(self, monkeypatch):
        monkeypatch.setenv('STRAVA_CLUB_IDS', '["1793883","9876543"]')
        monkeypatch.setenv('STRAVA_REFRESH_TOKEN', 'token')
        config = reload_config(monkeypatch)
        assert config.STRAVA_CLUB_IDS == ["1793883", "9876543"]

    def test_parse_single_club_json(self, monkeypatch):
        monkeypatch.setenv('STRAVA_CLUB_IDS', '["1793883"]')
        monkeypatch.setenv('STRAVA_REFRESH_TOKEN', 'token')
        config = reload_config(monkeypatch)
        assert config.STRAVA_CLUB_IDS == ["1793883"]
        assert len(config.STRAVA_CLUB_IDS) == 1

    def test_parse_invalid_json_defaults_to_empty(self, monkeypatch):
        monkeypatch.setenv('STRAVA_CLUB_IDS', 'not-valid-json')
        monkeypatch.setenv('STRAVA_REFRESH_TOKEN', 'token')
        config = reload_config(monkeypatch)
        assert config.STRAVA_CLUB_IDS == []

    def test_missing_env_var_defaults_to_empty(self, monkeypatch):
        monkeypatch.delenv('STRAVA_CLUB_IDS', raising=False)
        monkeypatch.setenv('STRAVA_REFRESH_TOKEN', 'token')
        config = reload_config(monkeypatch)
        assert config.STRAVA_CLUB_IDS == []

    def test_empty_json_array(self, monkeypatch):
        monkeypatch.setenv('STRAVA_CLUB_IDS', '[]')
        monkeypatch.setenv('STRAVA_REFRESH_TOKEN', 'token')
        config = reload_config(monkeypatch)
        assert config.STRAVA_CLUB_IDS == []


class TestTableNames:
    def test_default_activities_table(self, monkeypatch):
        monkeypatch.delenv('DYNAMODB_TABLE_NAME', raising=False)
        monkeypatch.setenv('STRAVA_CLUB_IDS', '[]')
        config = reload_config(monkeypatch)
        assert config.DYNAMODB_TABLE_NAME == 'ACTIVUM_ACT'

    def test_default_athletes_table(self, monkeypatch):
        monkeypatch.delenv('ATHLETES_TABLE_NAME', raising=False)
        monkeypatch.setenv('STRAVA_CLUB_IDS', '[]')
        config = reload_config(monkeypatch)
        assert config.ATHLETES_TABLE_NAME == 'ACTIVUM_USR'

    def test_custom_table_names(self, monkeypatch):
        monkeypatch.setenv('DYNAMODB_TABLE_NAME', 'my-activities')
        monkeypatch.setenv('ATHLETES_TABLE_NAME', 'my-athletes')
        monkeypatch.setenv('STRAVA_CLUB_IDS', '[]')
        config = reload_config(monkeypatch)
        assert config.DYNAMODB_TABLE_NAME == 'my-activities'
        assert config.ATHLETES_TABLE_NAME == 'my-athletes'
