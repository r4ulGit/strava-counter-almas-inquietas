"""Tests for api/services.py — dashboard data aggregation."""
import os
import sys
import pytest
from decimal import Decimal
from unittest.mock import patch

# IMPORTANT: api/ must come FIRST so 'import db/config/services' resolves to api/*
# and NOT worker/*. Both dirs have a 'database.py' but api now uses 'db.py'.
API_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'api'))
WORKER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'worker'))

# Ensure api is first — remove then re-insert at position 0
for d in [WORKER_DIR, API_DIR]:
    if d in sys.path:
        sys.path.remove(d)
sys.path.insert(0, API_DIR)


@pytest.fixture(autouse=True)
def api_env(monkeypatch):
    monkeypatch.setenv('ACTIVITIES_TABLE_NAME', 'ACTIVUM_ACT')
    monkeypatch.setenv('ATHLETES_TABLE_NAME', 'ACTIVUM_USR')
    monkeypatch.setenv('AWS_REGION', 'eu-west-1')
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'testing')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
    monkeypatch.setenv('GOAL_KM', '12000')
    monkeypatch.setenv('LAST_ACT', '3')
    monkeypatch.setenv('API_KEY', 'key')
    monkeypatch.setenv('API_SIGNING_SECRET', 'secret')
    monkeypatch.setenv('RATE_LIMIT_MAX', '30')
    monkeypatch.setenv('RATE_LIMIT_WINDOW', '60')
    monkeypatch.setenv('CORS_ALLOWED_ORIGINS', 'http://localhost:5173')
    monkeypatch.setenv('AUTH_TOLERANCE_SECONDS', '300')
    monkeypatch.setenv('TOKEN_TTL_SECONDS', '300')


SAMPLE_ACTIVITIES = [
    {
        'activity_id': 'id1',
        'title': 'Morning Run',
        'athlete': 'Daniel F.',
        'type': 'Run',
        'sport_type': 'Run',
        'distance_km': Decimal('10.03'),
        'moving_time_seconds': 3643,
        'start_date': '2026-05-30T08:00:00Z',
    },
    {
        'activity_id': 'id2',
        'title': 'Evening Ride',
        'athlete': 'Lucia L.',
        'type': 'Ride',
        'sport_type': 'Ride',
        'distance_km': Decimal('25.00'),
        'moving_time_seconds': 3600,
        'start_date': '2026-05-29T18:00:00Z',
    },
    {
        'activity_id': 'id3',
        'title': 'Quick Hike',
        'athlete': 'Daniel F.',
        'type': 'Hike',
        'sport_type': 'Hike',
        'distance_km': Decimal('8.50'),
        'moving_time_seconds': 5400,
        'start_date': '2026-05-28T10:00:00Z',
    },
    {
        'activity_id': 'id4',
        'title': 'Old Run',
        'athlete': 'Jose A.',
        'type': 'Run',
        'sport_type': 'Run',
        'distance_km': Decimal('5.00'),
        'moving_time_seconds': 1500,
        'start_date': '2026-05-01T07:00:00Z',
    },
]

SAMPLE_ATHLETES = [
    {'athlete_name': 'Lucia L.', 'currentKm': Decimal('25.00'), 'lastIncrement': Decimal('25.00')},
    {'athlete_name': 'Daniel F.', 'currentKm': Decimal('18.53'), 'lastIncrement': Decimal('10.03')},
    {'athlete_name': 'Jose A.', 'currentKm': Decimal('5.00'), 'lastIncrement': Decimal('5.00')},
]


def _load_svc():
    """Reload config + db + services fresh."""
    for mod_name in ['api_config', 'db', 'services']:
        if mod_name in sys.modules:
            del sys.modules[mod_name]
    import api_config as config  # noqa: F401
    import db      # noqa: F401
    import services as svc
    return svc


class TestBuildDashboardData:
    def test_total_km_sums_all_activity_types(self):
        svc = _load_svc()
        with patch.object(svc.db, 'get_all_activities', return_value=SAMPLE_ACTIVITIES), \
             patch.object(svc.db, 'get_top_athletes', return_value=SAMPLE_ATHLETES):
            result = svc.build_dashboard_data()
        # 10.03 + 25.00 + 8.50 + 5.00 = 48.53
        assert result['total_km'] == pytest.approx(48.53, abs=0.01)

    def test_total_activities_count(self):
        svc = _load_svc()
        with patch.object(svc.db, 'get_all_activities', return_value=SAMPLE_ACTIVITIES), \
             patch.object(svc.db, 'get_top_athletes', return_value=SAMPLE_ATHLETES):
            result = svc.build_dashboard_data()
        assert result['total_activities'] == 4

    def test_last_activities_ordered_newest_first(self):
        svc = _load_svc()
        with patch.object(svc.db, 'get_all_activities', return_value=SAMPLE_ACTIVITIES), \
             patch.object(svc.db, 'get_top_athletes', return_value=SAMPLE_ATHLETES):
            result = svc.build_dashboard_data()
        dates = [a['date'] for a in result['last_activities']]
        assert dates == sorted(dates, reverse=True)
        assert len(result['last_activities']) == 3  # LAST_ACT=3

    def test_last_activities_limited_by_last_act_env(self):
        svc = _load_svc()
        with patch.object(svc.db, 'get_all_activities', return_value=SAMPLE_ACTIVITIES), \
             patch.object(svc.db, 'get_top_athletes', return_value=SAMPLE_ATHLETES):
            result = svc.build_dashboard_data()
        import api_config as cfg
        assert len(result['last_activities']) <= cfg.LAST_ACT

    def test_top_athletes_sorted_by_current_km(self):
        svc = _load_svc()
        with patch.object(svc.db, 'get_all_activities', return_value=SAMPLE_ACTIVITIES), \
             patch.object(svc.db, 'get_top_athletes', return_value=SAMPLE_ATHLETES):
            result = svc.build_dashboard_data()
        kms = [a['currentKm'] for a in result['top_athletes']]
        assert kms == sorted(kms, reverse=True)

    def test_goal_km_in_config(self):
        svc = _load_svc()
        with patch.object(svc.db, 'get_all_activities', return_value=[]), \
             patch.object(svc.db, 'get_top_athletes', return_value=[]):
            result = svc.build_dashboard_data()
        assert result['config']['goal_km'] == 12000.0

    def test_empty_database_returns_zeros(self):
        svc = _load_svc()
        with patch.object(svc.db, 'get_all_activities', return_value=[]), \
             patch.object(svc.db, 'get_top_athletes', return_value=[]):
            result = svc.build_dashboard_data()
        assert result['total_km'] == 0.0
        assert result['total_activities'] == 0
        assert result['top_athletes'] == []
        assert result['last_activities'] == []
