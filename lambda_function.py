import requests
import os
import json
import boto3
from decimal import Decimal

# --- CONFIGURATION ---
STRAVA_CLIENT_ID = os.environ.get('STRAVA_CLIENT_ID')
STRAVA_CLIENT_SECRET = os.environ.get('STRAVA_CLIENT_SECRET')
STRAVA_REFRESH_TOKEN = os.environ.get('STRAVA_REFRESH_TOKEN')
DYNAMODB_TABLE_NAME = "strava_activities"

AUTH_URL = "https://www.strava.com/oauth/token"
ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"

# Initialize DynamoDB resource outside the handler for connection reuse
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

def refresh_access_token():
    """
    Retrieves a new access token using the refresh token.
    """
    print("🔄 Requesting new token from Strava...")
    payload = {
        'client_id': STRAVA_CLIENT_ID,
        'client_secret': STRAVA_CLIENT_SECRET,
        'refresh_token': STRAVA_REFRESH_TOKEN,
        'grant_type': "refresh_token"
    }

    act = {
        'id': 'TEST_ID_123',
        'name': 'TEST ACTIVITY',
        'type': 'Run',
        'distance': 10000,
        'moving_time': 3600,
        'start_date': '2025-11-25T10:00:00Z',
        'kudos_count': 5
    }
    
    try:
        response = requests.post(AUTH_URL, data=payload)
        response.raise_for_status()
        print("✅ Token refreshed successfully.")
        return response.json()['access_token']
    except requests.exceptions.RequestException as e:
        print(f"❌ Error refreshing token: {e}")
        save_activity_to_db(act)
        print(f"✅ TEST item saved successfully.")
        return None

def get_activities(access_token):
    """
    Downloads the latest activities from the athlete.
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {'per_page': 10} # Fetching last 10 activities
    
    print("📡 Downloading activities...")
    try:
        response = requests.get(ACTIVITIES_URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")
        return []

def save_activity_to_db(activity):
    """
    Saves a single activity to DynamoDB.
    Prevents duplicates automatically if 'activity_id' already exists.
    """
    try:
        # DynamoDB requires Decimal for floats, or storing as String.
        # We process the item to match the table schema.
        item = {
            'activity_id': str(activity['id']),
            'name': activity.get('name', 'Unknown'),
            'type': activity.get('type', 'Unknown'),
            # Convert meters to km and store as Decimal
            'distance_km': Decimal(str(round(activity.get('distance', 0) / 1000, 2))),
            'moving_time_seconds': activity.get('moving_time', 0),
            'start_date': activity.get('start_date'),
            'kudos_count': activity.get('kudos_count', 0)
        }
        
        table.put_item(Item=item)
        print(f"💾 Saved: {item['name']} ({item['distance_km']} km)")
        return True
    except Exception as e:
        print(f"⚠️ Error saving activity {activity.get('id')}: {e}")
        return False

# --- AWS LAMBDA ENTRY POINT ---
def lambda_handler(event, context):
    print("🚀 Starting Strava Lambda execution...")
    
    if not all([STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN]):
        return {'statusCode': 500, 'body': 'Error: Missing AWS environment variables.'}

    # 1. Get Token
    token = refresh_access_token()
    if not token:
        return {'statusCode': 401, 'body': 'Strava authentication failed.'}

    # 2. Get Activities
    activities = get_activities(token)
    
    # 3. Save to DynamoDB
    saved_count = 0
    for act in activities:
        if save_activity_to_db(act):
            saved_count += 1

    message = f"Success! Processed {len(activities)} activities. Saved/Updated {saved_count} in DB."
    print(message)

    return {
        'statusCode': 200,
        'body': json.dumps(message)
    }