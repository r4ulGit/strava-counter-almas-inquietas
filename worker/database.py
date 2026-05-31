import boto3
import hashlib
from decimal import Decimal
from datetime import datetime
from botocore.exceptions import ClientError
import config

# Initialize DynamoDB Resource
dynamodb = boto3.resource('dynamodb', region_name=config.AWS_REGION)
activities_table = dynamodb.Table(config.DYNAMODB_TABLE_NAME)
athletes_table = dynamodb.Table(config.ATHLETES_TABLE_NAME)


def generate_synthetic_id(activity):
    """
    Generates a deterministic ID based on activity properties.
    Needed because the Strava Club API does not return activity IDs.
    Signature: Athlete + Name + Distance + MovingTime + ElapsedTime + Type
    """
    athlete = activity.get('athlete', {})
    athlete_name = f"{athlete.get('firstname', 'Unknown')}{athlete.get('lastname', '')}"

    raw_signature = (
        f"{athlete_name}_"
        f"{activity.get('name')}_"
        f"{activity.get('distance')}_"
        f"{activity.get('moving_time')}_"
        f"{activity.get('elapsed_time')}_"
        f"{activity.get('total_elevation_gain')}_"
        f"{activity.get('type')}_"
    )
    return hashlib.md5(raw_signature.encode('utf-8')).hexdigest()


def save_activity(activity):
    """
    Parses and saves a single activity into the ACTIVUM_ACT DynamoDB table.
    Uses a conditional write to prevent duplicates.

    Returns:
        True if the activity was saved (new), False if skipped or error.
    """
    try:
        # 1. Determine ID (synthetic since club API has none)
        activity_id = generate_synthetic_id(activity)

        # 2. Handle Date — club API does not return start_date
        start_date = activity.get('start_date')
        if not start_date:
            start_date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

        athlete = activity.get('athlete', {})

        # 3. Create Item
        item = {
            'activity_id': activity_id,
            'title': activity.get('name', 'Unknown'),
            'type': activity.get('type', 'Unknown'),
            'sport_type': activity.get('sport_type', activity.get('type', 'Unknown')),
            'athlete': f"{athlete.get('firstname', 'Unknown')} {athlete.get('lastname', '')}".strip(),
            'distance_km': Decimal(str(round(activity.get('distance', 0) / 1000, 2))),
            'moving_time_seconds': int(activity.get('moving_time', 0)),
            'total_elevation_gain': Decimal(str(round(activity.get('total_elevation_gain', 0), 1))),
            'start_date': start_date,
        }

        # 4. Insert with Condition (fail silently if exists)
        activities_table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(activity_id)'
        )

        print(f"💾 Saved NEW: {item['title']} by {item['athlete']} ({item['distance_km']} km)")
        return True

    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print(f"⏭️  Skipped (already exists): {activity.get('name')}")
            return False
        else:
            print(f"⚠️ DynamoDB Error saving activity: {e}")
            return False

    except Exception as e:
        print(f"⚠️ General Error saving activity: {e}")
        return False


def upsert_athlete(activity):
    """
    Updates the athlete's record in ACTIVUM_USR:
    - SET lastIncrement = this activity's distance_km
    - ADD currentKm += distance_km (atomic, prevents race conditions)

    Only called when an activity is confirmed NEW (save_activity returned True),
    ensuring we never double-count an athlete's km.

    Args:
        activity: A raw Strava Club API activity dict.
    """
    try:
        athlete = activity.get('athlete', {})
        athlete_name = f"{athlete.get('firstname', 'Unknown')} {athlete.get('lastname', '')}".strip()
        distance_km = Decimal(str(round(activity.get('distance', 0) / 1000, 2)))

        athletes_table.update_item(
            Key={'athlete_name': athlete_name},
            UpdateExpression='SET lastIncrement = :inc ADD currentKm :km',
            ExpressionAttributeValues={
                ':inc': distance_km,
                ':km': distance_km,
            }
        )
        print(f"👤 Updated athlete: {athlete_name} (+{distance_km} km)")

    except Exception as e:
        print(f"⚠️ Error updating athlete '{athlete_name}': {e}")