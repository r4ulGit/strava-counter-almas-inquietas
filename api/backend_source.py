import json
import os
import boto3
from pathlib import Path
from decimal import Decimal
from dotenv import load_dotenv

# --- VARIABLE LOADING ---
current_dir = Path(__file__).resolve().parent
env_path = current_dir / '.env'
load_dotenv(dotenv_path=env_path)

# --- CONFIGURATION ---
DYNAMODB_TABLE_NAME = os.getenv('DYNAMODB_TABLE_NAME', 'strava_activities')
AWS_REGION = os.getenv('AWS_REGION', 'eu-west-1')


TITLE_FILTER = os.getenv('TITLE_FILTER', 'Run')
try:
    GOAL_KM = float(os.getenv('GOAL_KM', 500))
except (ValueError, TypeError):
    GOAL_KM = 500.0

# Initialize DynamoDB resource
try:
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    table = dynamodb.Table(DYNAMODB_TABLE_NAME)
except Exception as e:
    print(f"❌ Error initializing DynamoDB: {e}")

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)

def get_all_activities():
    try:
        response = table.scan()
        data = response.get('Items', [])
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            data.extend(response.get('Items', []))
        return data
    except Exception as e:
        print(f"❌ Database Error: {str(e)}")
        raise e

def process_activities(event, context):
    print(f"🚀 API Request received. Filter: '{TITLE_FILTER}', Goal: {GOAL_KM}km")
    
    try:
        # 1. Fetch data
        items = get_all_activities()
        
        # 2. Filter, Sum and Collect
        total_km = 0
        match_count = 0
        filter_lower = TITLE_FILTER.lower()
        matched_activities = []
        
        for item in items:
            title = item.get('type', '').lower()
            
            # Dynamic filtering based on environment variable
            if filter_lower in title:
                distance = float(item.get('distance_km', 0))
                total_km += distance
                match_count += 1
                
                # Storing filtered activities details
                matched_activities.append({
                    "id": item.get('activity_id'),
                    "title": item.get('title'),
                    "athlete": item.get('athlete'),
                    "distance_km": distance,
                    "date": item.get('start_date')
                })
        
        print(f"📊 Result: {match_count} items with '{TITLE_FILTER}'. Total: {total_km} km.")

        # Sorting activities by date (from newest to oldest)
        matched_activities.sort(key=lambda x: x.get('date', ''), reverse=True)
        last_5_act = matched_activities[:5]

        # 3. Create Response (Including last 5 activities and config data)
        response_data = {
            "total_km": total_km,
            "matches_found": match_count,
            "last_5_act": last_5_act,
            "config": {
                "goal_km": GOAL_KM,
                "filter_word": TITLE_FILTER
            }
        }

        return {
            'statusCode': 200,
            'body': json.dumps(response_data, cls=DecimalEncoder)
        }

    except Exception as e:
        print(f"🔥 Critical Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
    print(f"🚀 API Request received. Filter: '{TITLE_FILTER}', Goal: {GOAL_KM}km")
    
    try:
        # 1. Fetch data
        items = get_all_activities()
        
        # 2. Filter and Sum
        total_km = 0
        match_count = 0
        filter_lower = TITLE_FILTER.lower()
        
        for item in items:
            title = item.get('type', '').lower()
            # Dynamic filtering based on environment variable
            if filter_lower in title:
                distance = float(item.get('distance_km', 0))
                total_km += distance
                match_count += 1
        
        print(f"📊 Result: {match_count} items with '{TITLE_FILTER}'. Total: {total_km} km.")

        # 3. Create Response (Including config data for Frontend)
        response_data = {
            "total_km": total_km,
            "matches_found": match_count,
            "config": {
                "goal_km": GOAL_KM,
                "filter_word": TITLE_FILTER
            }
        }

        return {
            'statusCode': 200,
            'body': json.dumps(response_data, cls=DecimalEncoder)
        }

    except Exception as e:
        print(f"🔥 Critical Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

# --- LOCAL SERVER ---
if __name__ == "__main__":
    try:
        from flask import Flask, Response
        from flask_cors import CORS
    except ImportError:
        print("❌ Error: Install Flask with 'pip install flask flask-cors'")
        exit(1)

    app = Flask(__name__)
    CORS(app) 

    print("\n🌍 STARTING LOCAL SERVER...")
    print(f"   👉 Config: Filter='{TITLE_FILTER}', Goal={GOAL_KM}km")
    print("   👉 Listening at: http://127.0.0.1:5000\n")

    @app.route("/", methods=['GET'])
    def local_handler():
        result = process_activities(None, None)
        return Response(
            response=result['body'], 
            status=result['statusCode'], 
            mimetype='application/json'
        )

    app.run(port=5000, debug=True)