import db
import api_config as config


def build_dashboard_data() -> dict:
    """
    Aggregates all data needed for the frontend dashboard:
    - Total km across ALL activity types (no filter)
    - Last LAST_ACT activities sorted newest-first
    - Top 10 athletes sorted by currentKm descending

    Returns:
        A dict matching the API response contract.
    """
    # Fetch all activities
    items = db.get_all_activities()

    # Sum ALL activities (no type filter)
    total_km = sum(float(item.get('distance_km', 0)) for item in items)
    total_activities = len(items)

    # Sort by date descending for recent activities
    items_sorted = sorted(
        items,
        key=lambda x: x.get('start_date', ''),
        reverse=True
    )
    last_activities = []
    for item in items_sorted[:config.LAST_ACT]:
        last_activities.append({
            "id": item.get('activity_id'),
            "title": item.get('title', 'Unknown'),
            "athlete": item.get('athlete', 'Unknown'),
            "type": item.get('type', 'Unknown'),
            "sport_type": item.get('sport_type', item.get('type', 'Unknown')),
            "distance_km": round(float(item.get('distance_km', 0)), 2),
            "moving_time_seconds": int(item.get('moving_time_seconds', 0)),
            "date": item.get('start_date', ''),
        })

    # Fetch top 10 athletes
    top_athletes_raw = db.get_top_athletes(limit=10)
    top_athletes = [
        {
            "athlete_name": a.get('athlete_name', 'Unknown'),
            "currentKm": round(float(a.get('currentKm', 0)), 2),
            "lastIncrement": round(float(a.get('lastIncrement', 0)), 2),
        }
        for a in top_athletes_raw
    ]

    return {
        "total_km": round(total_km, 2),
        "total_activities": total_activities,
        "top_athletes": top_athletes,
        "last_activities": last_activities,
        "config": {
            "goal_km": config.GOAL_KM,
        }
    }
