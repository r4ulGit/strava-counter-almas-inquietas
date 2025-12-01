import os
import json
import time
import requests
import boto3
import hashlib
from decimal import Decimal
from datetime import datetime
from dotenv import load_dotenv

# 1. Load environment variables
load_dotenv()

# --- CONFIGURATION ---
STRAVA_CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
STRAVA_CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
STRAVA_REFRESH_TOKEN = os.getenv('STRAVA_REFRESH_TOKEN')
STRAVA_CLUB_ID = os.getenv('STRAVA_CLUB_ID')
DYNAMODB_TABLE_NAME = os.getenv('DYNAMODB_TABLE_NAME', 'strava_activities')
AWS_REGION = os.getenv('AWS_REGION', 'eu-west-1')

AUTH_URL = "https://www.strava.com/oauth/token"
# Using the Club endpoint as configured
ACTIVITIES_URL = f"https://www.strava.com/api/v3/clubs/{STRAVA_CLUB_ID}/activities"

# Initialize DynamoDB Resource
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

def refresh_access_token():
    """
    Exchanges the refresh token for a new valid access token.
    """
    print("🔄 Requesting new access token from Strava...")
    payload = {
        'client_id': STRAVA_CLIENT_ID,
        'client_secret': STRAVA_CLIENT_SECRET,
        'refresh_token': STRAVA_REFRESH_TOKEN,
        'grant_type': "refresh_token"
    }
    
    try:
        response = requests.post(AUTH_URL, data=payload, timeout=10)
        response.raise_for_status()
        return response.json()['access_token']
    except Exception as e:
        print(f"❌ Authentication Error: {e}")
        return None

def get_strava_activities(access_token):
    """
    Fetches the most recent activities from the CLUB.
    Note: Club activities do NOT contain 'id' or 'start_date' for privacy reasons.
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {'per_page': 30} 
    
    try:
        response = requests.get(ACTIVITIES_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ API Error: {e}")
        return []

def generate_synthetic_id(activity):
    """
    Generates a unique deterministic ID for club activities because Strava 
    hides the real 'id' in this endpoint.
    Signature: AthleteName + ActivityName + Distance + MovingTime
    """
    athlete = activity.get('athlete', {})
    # Provide defaults in case fields are missing
    athlete_name = f"{athlete.get('firstname', 'Unknown')}{athlete.get('lastname', '')}"
    
    # Create a string unique to this specific effort
    # Example: "JuanPerez_MorningRun_10050.5_3600"
    raw_signature = f"{athlete_name}_{activity.get('name')}_{activity.get('distance')}_{activity.get('moving_time')}"
    
    # Create an MD5 hash of that string to get a clean ID
    return hashlib.md5(raw_signature.encode('utf-8')).hexdigest()

def save_activity(activity):
    """
    Parses and saves a single activity into DynamoDB.
    """
    try:
        # 1. GENERATE ID (Vital step for Club activities)
        # We prefer the real 'id' if available, otherwise we generate one.
        if 'id' in activity:
            activity_id = str(activity['id'])
        else:
            activity_id = generate_synthetic_id(activity)

        # 2. HANDLE DATE
        # Club feed does NOT return start_date. We use the current ingestion time as fallback.
        # Ideally, we only insert if it's new, so 'now' is acceptable for "when we saw it".
        start_date = activity.get('start_date')
        if not start_date:
            start_date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

        item = {
            'activity_id': activity_id,
            'name': activity.get('name', 'Unknown'),
            'type': activity.get('type', 'Unknown'),
            # Convert meters to kilometers (Decimal for DB precision)
            'distance_km': Decimal(str(round(activity.get('distance', 0) / 1000, 2))),
            'moving_time_seconds': int(activity.get('moving_time', 0)),
            'start_date': start_date,
            'kudos_count': int(activity.get('kudos_count', 0))
        }
        
        # 'put_item' will overwrite if the ID already exists (perfect for updating)
        table.put_item(Item=item)
        print(f"💾 Saved: {item['name']} (ID: {activity_id[:8]}...)")
        return True
    except Exception as e:
        print(f"⚠️ Error saving activity: {e}")
        return False

# --- MAIN HANDLER ---
def retrieve_strava_data_lambda(event, context):
    print("🚀 Starting Strava Club Worker...")
    
    if not STRAVA_REFRESH_TOKEN or not STRAVA_CLUB_ID:
        print("❌ Config Error: Missing env variables.")
        return {'statusCode': 500, 'body': 'Config Error'}

    # 1. Auth
    token = refresh_access_token()
    if not token:
        return {'statusCode': 401, 'body': 'Auth Failed'}

    # 2. Fetch
    activities = get_strava_activities(token)
    print(f"📡 Retrieved {len(activities)} activities from Club.")

    # 3. Save
    saved_count = 0
    for act in activities:
        if save_activity(act):
            saved_count += 1

    msg = f"Process completed. Processed {saved_count} activities."
    print(msg)

    return {
        'statusCode': 200,
        'body': json.dumps(msg)
    }

if __name__ == "__main__":
    retrieve_strava_data_lambda(None, None)