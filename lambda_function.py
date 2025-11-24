import requests
import os
import json
import time

# --- CONFIGURATION ---
# AWS will automatically inject these environment variables 
# based on what you configured in the Lambda console.
STRAVA_CLIENT_ID = os.environ.get('STRAVA_CLIENT_ID')
STRAVA_CLIENT_SECRET = os.environ.get('STRAVA_CLIENT_SECRET')
STRAVA_REFRESH_TOKEN = os.environ.get('STRAVA_REFRESH_TOKEN')

AUTH_URL = "https://www.strava.com/oauth/token"
ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"

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
    
    response = requests.post(AUTH_URL, data=payload)
    
    if response.status_code == 200:
        print("✅ Token refreshed successfully.")
        return response.json()['access_token']
    else:
        print(f"❌ Error refreshing token: {response.text}")
        return None

def get_activities(access_token):
    """
    Downloads the latest activities from the athlete.
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # We request only 5 activities for testing purposes
    params = {'per_page': 5} 
    
    print("📡 Downloading activities...")
    response = requests.get(ACTIVITIES_URL, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ API Error: {response.text}")
        return []

# --- AWS LAMBDA ENTRY POINT ---
def lambda_handler(event, context):
    """
    This is the function AWS executes when the Lambda is triggered.
    """
    print("🚀 Starting Strava Lambda execution...")
    
    # 1. Validate that environment variables are present
    if not all([STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN]):
        return {
            'statusCode': 500,
            'body': 'Error: Missing AWS environment variables.'
        }

    # 2. Get Access Token
    token = refresh_access_token()
    if not token:
        return {'statusCode': 401, 'body': 'Strava authentication failed.'}

    # 3. Get Activities
    activities = get_activities(token)
    
    # 4. Process and Log (Simulation)
    summary = []
    for act in activities:
        # Distance is in meters, converting to km
        info = f"🏃 {act['type']} - {act['name']} ({act['distance']/1000:.2f} km)"
        
        # This print statement will appear in AWS CloudWatch logs
        print(info) 
        summary.append(info)

    return {
        'statusCode': 200,
        'body': json.dumps(f"Success! Processed {len(summary)} activities: {summary}")
    }