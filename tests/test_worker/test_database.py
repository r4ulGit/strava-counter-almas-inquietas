"""Tests for worker/database.py — save_activity and upsert_athlete."""
import os
import sys
import pytest
import boto3
from decimal import Decimal
from moto import mock_aws
from unittest.mock import patch

# Ensure worker directory is on the path
WORKER_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'worker'))
if WORKER_DIR not in sys.path:
    sys.path.insert(0, WORKER_DIR)


@pytest.fixture
def aws_mock_env(monkeypatch):
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'eu-west-1')
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'testing')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
    monkeypatch.setenv('ACTIVITIES_TABLE_NAME', 'ACTIVUM_ACT')
    monkeypatch.setenv('ATHLETES_TABLE_NAME', 'ACTIVUM_USR')
    monkeypatch.setenv('AWS_REGION', 'eu-west-1')
    monkeypatch.setenv('STRAVA_CLUB_IDS', '[]')
    monkeypatch.setenv('STRAVA_REFRESH_TOKEN', 'tok')


ACTIVITY_A = {
    'athlete': {'firstname': 'Daniel', 'lastname': 'F.'},
    'name': 'Morning Run',
    'distance': 10026.2,
    'moving_time': 3643,
    'elapsed_time': 3838,
    'total_elevation_gain': 113.4,
    'type': 'Run',
    'sport_type': 'Run',
}

ACTIVITY_B = {
    'athlete': {'firstname': 'Lucia', 'lastname': 'L.'},
    'name': 'Evening Ride',
    'distance': 25000.0,
    'moving_time': 3600,
    'elapsed_time': 3700,
    'total_elevation_gain': 200.0,
    'type': 'Ride',
    'sport_type': 'Ride',
}


@mock_aws
class TestGenerateSyntheticId:
    def test_deterministic(self, aws_mock_env):
        import importlib, config as cfg
        import database as db_module
        importlib.reload(cfg)
        importlib.reload(db_module)
        id1 = db_module.generate_synthetic_id(ACTIVITY_A)
        id2 = db_module.generate_synthetic_id(ACTIVITY_A)
        assert id1 == id2
        assert len(id1) == 32  # MD5 hex

    def test_different_activities_give_different_ids(self, aws_mock_env):
        import importlib, config as cfg
        import database as db_module
        importlib.reload(cfg)
        importlib.reload(db_module)
        id_a = db_module.generate_synthetic_id(ACTIVITY_A)
        id_b = db_module.generate_synthetic_id(ACTIVITY_B)
        assert id_a != id_b


@mock_aws
class TestSaveActivity:
    def _setup_tables(self):
        ddb = boto3.resource('dynamodb', region_name='eu-west-1')
        act_table = ddb.create_table(
            TableName='ACTIVUM_ACT',
            KeySchema=[{'AttributeName': 'activity_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'activity_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST',
        )
        usr_table = ddb.create_table(
            TableName='ACTIVUM_USR',
            KeySchema=[{'AttributeName': 'athlete_name', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'athlete_name', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST',
        )
        act_table.meta.client.get_waiter('table_exists').wait(TableName='ACTIVUM_ACT')
        usr_table.meta.client.get_waiter('table_exists').wait(TableName='ACTIVUM_USR')
        return act_table, usr_table

    def test_save_new_activity_returns_true(self, aws_mock_env):
        self._setup_tables()
        import importlib, config as cfg
        import database as db_module
        importlib.reload(cfg)
        importlib.reload(db_module)
        result = db_module.save_activity(ACTIVITY_A)
        assert result is True

    def test_save_duplicate_returns_false(self, aws_mock_env):
        self._setup_tables()
        import importlib, config as cfg
        import database as db_module
        importlib.reload(cfg)
        importlib.reload(db_module)
        db_module.save_activity(ACTIVITY_A)
        result = db_module.save_activity(ACTIVITY_A)
        assert result is False

    def test_saved_item_has_correct_fields(self, aws_mock_env):
        act_table, _ = self._setup_tables()
        import importlib, config as cfg
        import database as db_module
        importlib.reload(cfg)
        importlib.reload(db_module)
        db_module.save_activity(ACTIVITY_A)

        activity_id = db_module.generate_synthetic_id(ACTIVITY_A)
        item = act_table.get_item(Key={'activity_id': activity_id})['Item']

        assert item['athlete'] == 'Daniel F.'
        assert item['type'] == 'Run'
        assert float(item['distance_km']) == pytest.approx(10.03, abs=0.1)

    def test_save_two_different_activities(self, aws_mock_env):
        self._setup_tables()
        import importlib, config as cfg
        import database as db_module
        importlib.reload(cfg)
        importlib.reload(db_module)
        r1 = db_module.save_activity(ACTIVITY_A)
        r2 = db_module.save_activity(ACTIVITY_B)
        assert r1 is True
        assert r2 is True


@mock_aws
class TestUpsertAthlete:
    def _setup_tables(self):
        ddb = boto3.resource('dynamodb', region_name='eu-west-1')
        act_table = ddb.create_table(
            TableName='ACTIVUM_ACT',
            KeySchema=[{'AttributeName': 'activity_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'activity_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST',
        )
        usr_table = ddb.create_table(
            TableName='ACTIVUM_USR',
            KeySchema=[{'AttributeName': 'athlete_name', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'athlete_name', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST',
        )
        act_table.meta.client.get_waiter('table_exists').wait(TableName='ACTIVUM_ACT')
        usr_table.meta.client.get_waiter('table_exists').wait(TableName='ACTIVUM_USR')
        return act_table, usr_table

    def test_creates_new_athlete_record(self, aws_mock_env):
        _, usr_table = self._setup_tables()
        import importlib, config as cfg
        import database as db_module
        importlib.reload(cfg)
        importlib.reload(db_module)
        db_module.upsert_athlete(ACTIVITY_A)

        item = usr_table.get_item(Key={'athlete_name': 'Daniel F.'})['Item']
        assert 'currentKm' in item
        assert float(item['currentKm']) == pytest.approx(10.03, abs=0.1)
        assert float(item['lastIncrement']) == pytest.approx(10.03, abs=0.1)

    def test_increments_existing_athlete_km(self, aws_mock_env):
        _, usr_table = self._setup_tables()
        import importlib, config as cfg
        import database as db_module
        importlib.reload(cfg)
        importlib.reload(db_module)
        db_module.upsert_athlete(ACTIVITY_A)
        db_module.upsert_athlete(ACTIVITY_A)  # second activity = same athlete

        item = usr_table.get_item(Key={'athlete_name': 'Daniel F.'})['Item']
        assert float(item['currentKm']) == pytest.approx(20.05, abs=0.1)

    def test_updates_last_increment(self, aws_mock_env):
        _, usr_table = self._setup_tables()
        import importlib, config as cfg
        import database as db_module
        importlib.reload(cfg)
        importlib.reload(db_module)
        db_module.upsert_athlete(ACTIVITY_A)

        activity_b_same_athlete = {**ACTIVITY_B, 'athlete': {'firstname': 'Daniel', 'lastname': 'F.'}}
        db_module.upsert_athlete(activity_b_same_athlete)

        item = usr_table.get_item(Key={'athlete_name': 'Daniel F.'})['Item']
        # lastIncrement should reflect the most recent activity (25 km)
        assert float(item['lastIncrement']) == pytest.approx(25.0, abs=0.1)
        # currentKm should be the total
        assert float(item['currentKm']) == pytest.approx(35.03, abs=0.2)
