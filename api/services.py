import db
import api_config as config


def build_dashboard_data() -> dict:
    """
    Aggregates all data needed for the frontend dashboard:
    - Total km across filtered activities
    - Last LAST_ACT filtered activities sorted newest-first
    - Top 10 athletes sorted by currentKm descending (recalculated from filtered activities)

    Returns:
        A dict matching the API response contract.
    """
    # Fetch all activities from DynamoDB
    items = db.get_all_activities()

    # Apply filters
    filtered_items = []
    for item in items:
        # 1. Type Filter
        if config.ACT_TYPE_FILTER:
            itype = item.get('type') or ''
            isport = item.get('sport_type') or ''
            if itype not in config.ACT_TYPE_FILTER and isport not in config.ACT_TYPE_FILTER:
                continue

        # 2. Title Filter
        if config.ACT_TITLE_FILTER:
            title = item.get('title') or ''
            if config.ACT_TITLE_FILTER.lower() not in title.lower():
                continue

        # 3. Start Date Filter
        if config.START_DATE:
            start_date = item.get('start_date') or ''
            if start_date < config.START_DATE:
                continue

        filtered_items.append(item)

    # Sum filtered activities
    total_km = sum(float(item.get('distance_km', 0)) for item in filtered_items)
    total_activities = len(filtered_items)

    # Sort by date descending for recent activities
    items_sorted = sorted(
        filtered_items,
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

    # Calculate top 10 athletes dynamically based on filtered activities
    athlete_stats = {}  # athlete_name -> { 'total_km': float, 'newest_date': str, 'newest_dist': float }
    for item in filtered_items:
        athlete_name = item.get('athlete')
        if not athlete_name or athlete_name == 'Unknown':
            continue
        dist = float(item.get('distance_km', 0))
        date = item.get('start_date', '')

        if athlete_name not in athlete_stats:
            athlete_stats[athlete_name] = {
                'total_km': dist,
                'newest_date': date,
                'newest_dist': dist
            }
        else:
            athlete_stats[athlete_name]['total_km'] += dist
            if date > athlete_stats[athlete_name]['newest_date']:
                athlete_stats[athlete_name]['newest_date'] = date
                athlete_stats[athlete_name]['newest_dist'] = dist

    # Format and sort top 10 athletes
    top_athletes = []
    for athlete_name, stats in athlete_stats.items():
        top_athletes.append({
            "athlete_name": athlete_name,
            "currentKm": round(stats['total_km'], 2),
            "lastIncrement": round(stats['newest_dist'], 2)
        })
    top_athletes.sort(key=lambda x: x['currentKm'], reverse=True)
    top_athletes = top_athletes[:10]

    return {
        "total_km": round(total_km, 2),
        "total_activities": total_activities,
        "top_athletes": top_athletes,
        "last_activities": last_activities,
        "config": {
            "goal_km": config.GOAL_KM,
            "title": config.TITLE,
        }
    }
