import requests
import config

def refresh_access_token():
    """
    Exchanges the refresh token for a new valid access token.
    """
    print("🔄 Requesting new access token from Strava...")
    payload = {
        'client_id': config.STRAVA_CLIENT_ID,
        'client_secret': config.STRAVA_CLIENT_SECRET,
        'refresh_token': config.STRAVA_REFRESH_TOKEN,
        'grant_type': "refresh_token"
    }
    
    try:
        response = requests.post(config.AUTH_URL, data=payload, timeout=10)
        response.raise_for_status()
        return response.json()['access_token']
    except Exception as e:
        print(f"❌ Authentication Error: {e}")
        if 'response' in locals():
            print(f"   Auth Response: {response.text}")
        return None

def get_strava_activities(access_token):
    """
    Fetches the most recent activities from the CLUB.
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    # Request 200 activities (max allowed per page)
    params = {'per_page': 200}
    
    print(f"📡 Fetching URL: {config.ACTIVITIES_URL}")
    
    try:
        response = requests.get(config.ACTIVITIES_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ API Error: {e}")
        if 'response' in locals():
             print(f"   API Response Body: {response.text}")
        return []