import json
import os
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key

# --- CONFIGURATION ---
DYNAMODB_TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'strava_activities')

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1') # Adjust region if needed
table = dynamodb.Table(DYNAMODB_TABLE_NAME)

class DecimalEncoder(json.JSONEncoder):
    """
    Helper class to convert DynamoDB Decimal types to standard Python floats/ints
    so they can be serialized to JSON.
    """
    def default(self, obj):
        if isinstance(obj, Decimal):
            # Check if it's an integer or a float
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)

def get_all_activities():
    """
    Scans the table to return all activities.
    For production with thousands of items, 'Query' is better than 'Scan'.
    For a personal project, 'Scan' is perfectly fine and free.
    """
    try:
        response = table.scan()
        data = response.get('Items', [])
        
        # Handling pagination if data > 1MB (Optional but good practice)
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            data.extend(response.get('Items', []))
            
        # Sort by date descending (newest first)
        # We assume start_date is in ISO format (YYYY-MM-DD...) which sorts correctly as string
        data.sort(key=lambda x: x.get('start_date', ''), reverse=True)
        
        return data
    except Exception as e:
        print(f"❌ Database Error: {str(e)}")
        raise e

def process_activities(event, context):
    print("🚀 API Request received")
    
    try:
        # 1. Fetch data from DB
        items = get_all_activities()
        
        print(f"✅ Retrieved {len(items)} items from DB.")

        # 2. Return HTTP Response
        return {
            'statusCode': 200,
            'body': json.dumps(items, cls=DecimalEncoder)
        }

    except Exception as e:
        print(f"🔥 Critical Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }