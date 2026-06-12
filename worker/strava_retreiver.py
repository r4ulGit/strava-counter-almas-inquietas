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

    # 2. Fetch from all clubs
    club_activities = []
    total_fetched = 0

    for club_id in config.STRAVA_CLUB_IDS:
        print(f"\n📦 Fetching Club ID: {club_id}")
        activities = strava_client.get_club_activities(token, club_id)
        print(f"   Retrieved {len(activities)} activities from club {club_id}")
        total_fetched += len(activities)
        club_activities.append(activities)

    # 3. Interweave the activities from different clubs (oldest to newest relative order)
    interweaved = []
    max_len = max(len(lst) for lst in club_activities) if club_activities else 0
    # Loop backwards from oldest (max_len - 1) to newest (0)
    for i in range(max_len - 1, -1, -1):
        for lst in club_activities:
            if i < len(lst):
                interweaved.append(lst[i])

    # 4. Save activities and update athletes with sequential timestamps
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    total_saved = 0

    for idx, act in enumerate(interweaved):
        if not act.get('start_date'):
            offset = len(interweaved) - 1 - idx
            act['start_date'] = (now - timedelta(minutes=offset)).strftime('%Y-%m-%dT%H:%M:%SZ')

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