import json
import config
import strava_client
import database


# --- MAIN HANDLER ---
def retrieve_strava_data_lambda(event, context):
    print("🚀 Starting ACTIVUM Multi-Club Worker...")

    # Validation
    if not config.STRAVA_REFRESH_TOKEN:
        print("❌ Config Error: Missing STRAVA_REFRESH_TOKEN.")
        return {'statusCode': 500, 'body': 'Config Error: Missing STRAVA_REFRESH_TOKEN'}

    if not config.STRAVA_CLUB_IDS:
        print("❌ Config Error: STRAVA_CLUB_IDS is empty or not set.")
        return {'statusCode': 500, 'body': 'Config Error: STRAVA_CLUB_IDS is empty'}

    print(f"🔍 Configured clubs: {config.STRAVA_CLUB_IDS}")

    # 1. Auth — a single token is reused for all clubs
    token = strava_client.refresh_access_token()
    if not token:
        return {'statusCode': 401, 'body': 'Auth Failed'}

    # 2. Fetch from each club, save activities, update athletes
    total_saved = 0
    total_fetched = 0

    for club_id in config.STRAVA_CLUB_IDS:
        print(f"\n📦 Processing Club ID: {club_id}")
        activities = strava_client.get_club_activities(token, club_id)
        total_fetched += len(activities)
        print(f"   Retrieved {len(activities)} activities from club {club_id}")

        for act in activities:
            was_new = database.save_activity(act)
            if was_new:
                total_saved += 1
                database.upsert_athlete(act)

    msg = (
        f"Process completed. "
        f"Clubs processed: {len(config.STRAVA_CLUB_IDS)}. "
        f"Activities fetched: {total_fetched}. "
        f"New activities saved: {total_saved}."
    )
    print(f"\n✅ {msg}")

    return {'statusCode': 200, 'body': json.dumps(msg)}


# Allow local execution
if __name__ == "__main__":
    retrieve_strava_data_lambda(None, None)