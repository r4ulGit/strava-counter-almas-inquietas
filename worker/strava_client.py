import requests
import config


def refresh_access_token():
    """
    Exchanges the refresh token for a new valid access token.
    The same token is used to access all clubs.
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


def get_club_activities(access_token, club_id):
    """
    Fetches the most recent activities from a specific Strava CLUB.
    Paginates through all available pages (200 per page).

    Args:
        access_token: A valid Strava OAuth access token.
        club_id: The numeric ID of the Strava club.

    Returns:
        A list of activity dicts from the Strava Club API.
        Note: Club activities do NOT include activity_id, polyline, or kudos.
    """
    url = config.ACTIVITIES_URL_TEMPLATE.format(club_id=club_id)
    headers = {'Authorization': f'Bearer {access_token}'}
    all_activities = []
    page = 1

    print(f"📡 Fetching activities from Club ID: {club_id}")

    while True:
        params = {'per_page': 200, 'page': page}
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if not data:
                break  # No more pages
            all_activities.extend(data)
            print(f"   Page {page}: {len(data)} activities")
            if len(data) < 200:
                break  # Last page (fewer than max returned)
            page += 1
        except Exception as e:
            print(f"❌ API Error fetching club {club_id} page {page}: {e}")
            if 'response' in locals():
                print(f"   API Response Body: {response.text}")
            break

    return all_activities