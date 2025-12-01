import json
import config
import strava_client
import database

# --- MAIN HANDLER ---
def retrieve_strava_data_lambda(event, context):
    print("🚀 Starting Strava Club Worker...")
    
    # Debug config
    print(f"🔍 CONFIG CHECK: Club ID='{config.STRAVA_CLUB_ID}'")

    # Validation
    if not config.STRAVA_REFRESH_TOKEN or not config.STRAVA_CLUB_ID:
        print("❌ Config Error: Missing env variables.")
        return {'statusCode': 500, 'body': 'Config Error'}

    # 1. Auth (using strava_client)
    token = strava_client.refresh_access_token()
    if not token:
        return {'statusCode': 401, 'body': 'Auth Failed'}

    # 2. Fetch (using strava_client)
    activities = strava_client.get_strava_activities(token)
    print(f"📡 Retrieved {len(activities)} activities from Club.")

    # 3. Save (using database)
    saved_count = 0
    for act in activities:
        if database.save_activity(act):
            saved_count += 1

    msg = f"Process completed. New activities saved: {saved_count}."
    print(msg)

    return {'statusCode': 200, 'body': json.dumps(msg)}

# Allow local execution
if __name__ == "__main__":
    retrieve_strava_data_lambda(None, None)