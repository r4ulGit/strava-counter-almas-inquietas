import os
import json
import requests
import boto3
import hashlib
from botocore.exceptions import ClientError
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
# Construct URL (Handle None safely to avoid crash at import time)
club_id_safe = STRAVA_CLUB_ID if STRAVA_CLUB_ID else "UNKNOWN_CLUB_ID"
ACTIVITIES_URL = f"https://www.strava.com/api/v3/clubs/{club_id_safe}/activities"

# Initialize DynamoDB Resource
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

def refresh_access_token():
    """ Exchanges the refresh token for a new valid access token. """
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
        # DEBUG: Print detailed response if possible
        if 'response' in locals():
            print(f"   Auth Response: {response.text}")
        return None

def get_strava_activities(access_token):
    """ Fetches the most recent activities from the CLUB. """
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {'per_page': 200}
    
    print(f"📡 Fetching URL: {ACTIVITIES_URL}")
    
    try:
        response = requests.get(ACTIVITIES_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ API Error: {e}")
        if 'response' in locals():
             print(f"   API Response Body: {response.text}")
        return []

# ... (Las funciones generate_synthetic_id y save_activity se mantienen igual) ...
def generate_synthetic_id(activity):
    athlete = activity.get('athlete', {})
    athlete_name = f"{athlete.get('firstname', 'Unknown')}{athlete.get('lastname', '')}"
    raw_signature = f"{athlete_name}_{activity.get('name')}_{activity.get('distance')}_{activity.get('moving_time')}"
    return hashlib.md5(raw_signature.encode('utf-8')).hexdigest()

def save_activity(activity):
    """
    Saves an activity ONLY if it doesn't exist yet (preserving the original insertion date).
    """
    try:
        # 1. Determine ID
        if 'id' in activity:
            activity_id = str(activity['id'])
        else:
            activity_id = generate_synthetic_id(activity)

        # 2. Handle Date
        # Since we skip duplicates, this date represents "First Seen At"
        start_date = activity.get('start_date')
        if not start_date:
            start_date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

        item = {
            'activity_id': activity_id,
            'name': activity.get('name', 'Unknown'),
            'type': activity.get('type', 'Unknown'),
            'distance_km': Decimal(str(round(activity.get('distance', 0) / 1000, 2))),
            'moving_time_seconds': int(activity.get('moving_time', 0)),
            'start_date': start_date
        }
        
        # 3. Insert with Condition (Fail if exists)
        table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(activity_id)'
        )
        
        print(f"💾 Saved NEW: {item['name']} (ID: {activity_id[:8]}...)")
        return True

    except ClientError as e:
        # Ignore if the error is just "Item already exists"
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            # Optional: Uncomment next line to log skipped items
            # print(f"⏭️ Skipped (Already exists): {activity.get('name')}")
            return False
        else:
            print(f"⚠️ DynamoDB Error: {e}")
            return False
            
    except Exception as e:
        print(f"⚠️ General Error saving activity: {e}")
        return False

# --- MAIN HANDLER ---
def retrieve_strava_data_lambda(event, context):
    print("🚀 Starting Strava Club Worker...")
    
    # --- DEBUGGING BLOCK ---
    print(f"🔍 DEBUG CONFIGURATION:")
    print(f"   - Club ID (Raw): '{STRAVA_CLUB_ID}'")
    print(f"   - Target URL: {ACTIVITIES_URL}")
    if STRAVA_REFRESH_TOKEN:
        print(f"   - Refresh Token: {STRAVA_REFRESH_TOKEN[:5]}... (Length: {len(STRAVA_REFRESH_TOKEN)})")
    else:
        print("   - Refresh Token: NONE/MISSING")
    # ---------------------

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

    return {'statusCode': 200, 'body': json.dumps(msg)}

if __name__ == "__main__":
    retrieve_strava_data_lambda(None, None)