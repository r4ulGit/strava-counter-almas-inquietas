"""
Shared pytest fixtures for ACTIVUM unit tests.
Uses moto to mock AWS DynamoDB — no real AWS calls are made.
"""
import os
import pytest
import boto3
from moto import mock_aws


# ---------------------------------------------------------------------------
# Environment setup — must be set BEFORE any app modules are imported
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch):
    """Set required environment variables for every test."""
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'eu-west-1')
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'testing')
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'testing')
    monkeypatch.setenv('AWS_SECURITY_TOKEN', 'testing')
    monkeypatch.setenv('AWS_SESSION_TOKEN', 'testing')
    monkeypatch.setenv('ACTIVITIES_TABLE_NAME', 'ACTIVUM_ACT')
    monkeypatch.setenv('ATHLETES_TABLE_NAME', 'ACTIVUM_USR')
    monkeypatch.setenv('AWS_REGION', 'eu-west-1')
    monkeypatch.setenv('GOAL_KM', '12000')
    monkeypatch.setenv('LAST_ACT', '5')
    monkeypatch.setenv('API_KEY', 'test-api-key')
    monkeypatch.setenv('API_SIGNING_SECRET', 'test-signing-secret-1234567890abcdef')
    monkeypatch.setenv('AUTH_TOLERANCE_SECONDS', '300')
    monkeypatch.setenv('TOKEN_TTL_SECONDS', '300')
    monkeypatch.setenv('RATE_LIMIT_MAX', '10')
    monkeypatch.setenv('RATE_LIMIT_WINDOW', '60')


# ---------------------------------------------------------------------------
# Mocked DynamoDB — Activities table
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_activities_table():
    """Creates a mocked ACTIVUM_ACT DynamoDB table and returns the table resource."""
    with mock_aws():
        dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
        table = dynamodb.create_table(
            TableName='ACTIVUM_ACT',
            KeySchema=[{'AttributeName': 'activity_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'activity_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST',
        )
        table.meta.client.get_waiter('table_exists').wait(TableName='ACTIVUM_ACT')
        yield table


@pytest.fixture
def mock_athletes_table():
    """Creates a mocked ACTIVUM_USR DynamoDB table and returns the table resource."""
    with mock_aws():
        dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
        table = dynamodb.create_table(
            TableName='ACTIVUM_USR',
            KeySchema=[{'AttributeName': 'athlete_name', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'athlete_name', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST',
        )
        table.meta.client.get_waiter('table_exists').wait(TableName='ACTIVUM_USR')
        yield table


@pytest.fixture
def mock_both_tables():
    """Creates both mocked DynamoDB tables within the same mock_aws context."""
    with mock_aws():
        dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')

        act_table = dynamodb.create_table(
            TableName='ACTIVUM_ACT',
            KeySchema=[{'AttributeName': 'activity_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'activity_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST',
        )
        usr_table = dynamodb.create_table(
            TableName='ACTIVUM_USR',
            KeySchema=[{'AttributeName': 'athlete_name', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'athlete_name', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST',
        )
        act_table.meta.client.get_waiter('table_exists').wait(TableName='ACTIVUM_ACT')
        usr_table.meta.client.get_waiter('table_exists').wait(TableName='ACTIVUM_USR')
        yield act_table, usr_table


# ---------------------------------------------------------------------------
# Sample activity data
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_activity():
    """A sample Strava Club API activity dict."""
    return {
        'athlete': {'firstname': 'Daniel', 'lastname': 'F.'},
        'name': 'Morning Run',
        'distance': 10026.2,
        'moving_time': 3643,
        'elapsed_time': 3838,
        'total_elevation_gain': 113.4,
        'type': 'Run',
        'sport_type': 'Run',
    }


@pytest.fixture
def sample_activity_2():
    """A second distinct sample activity."""
    return {
        'athlete': {'firstname': 'Lucia', 'lastname': 'L.'},
        'name': 'Evening Ride',
        'distance': 25000.0,
        'moving_time': 3600,
        'elapsed_time': 3700,
        'total_elevation_gain': 200.0,
        'type': 'Ride',
        'sport_type': 'Ride',
    }
