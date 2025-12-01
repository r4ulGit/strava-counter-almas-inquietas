import boto3
import hashlib
from decimal import Decimal
from datetime import datetime
from botocore.exceptions import ClientError
import config

# Initialize DynamoDB Resource
dynamodb = boto3.resource('dynamodb', region_name=config.AWS_REGION)
table = dynamodb.Table(config.DYNAMODB_TABLE_NAME)

def generate_synthetic_id(activity):
    """
    Generates a deterministic ID based on activity properties.
    """
    athlete = activity.get('athlete', {})
    athlete_name = f"{athlete.get('firstname', 'Unknown')}{athlete.get('lastname', '')}"
    
    raw_signature = f"{athlete_name}_{activity.get('name')}_{activity.get('distance')}_{activity.get('moving_time')}"
    return hashlib.md5(raw_signature.encode('utf-8')).hexdigest()

def save_activity(activity):
    """
    Parses and saves a single activity into DynamoDB.
    Returns True if saved, False if skipped or error.
    """
    try:
        # 1. Determine ID
        if 'id' in activity:
            activity_id = str(activity['id'])
        else:
            activity_id = generate_synthetic_id(activity)

        # 2. Handle Date
        start_date = activity.get('start_date')
        if not start_date:
            start_date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        athlete = activity.get('athlete', {})

        # 3. Create Item
        item = {
            'activity_id': activity_id,
            'title': activity.get('name', 'Unknown'),
            'type': activity.get('type', 'Unknown'),
            'athlete': f"{athlete.get('firstname', 'Unknown')} {athlete.get('lastname', '')}",
            'distance_km': Decimal(str(round(activity.get('distance', 0) / 1000, 2))),
            'moving_time_seconds': int(activity.get('moving_time', 0)),
            'start_date': start_date
        }
        
        # 4. Insert with Condition (Fail if exists to preserve original date)
        table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(activity_id)'
        )
        
        print(f"💾 Saved NEW: {item['title']} (ID: {activity_id[:8]}...)")
        return True

    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print(f"⏭️ Skipped (Already exists): {activity.get('name')}")
            # Item exists, silently skip
            return False
        else:
            print(f"⚠️ DynamoDB Error: {e}")
            return False
            
    except Exception as e:
        print(f"⚠️ General Error saving activity: {e}")
        return False