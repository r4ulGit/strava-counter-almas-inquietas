import os
import json
from dotenv import load_dotenv

# Load environment variables (for local testing)
load_dotenv()

# --- Strava OAuth (shared across all clubs) ---
STRAVA_CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
STRAVA_CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
STRAVA_REFRESH_TOKEN = os.getenv('STRAVA_REFRESH_TOKEN')

# --- Multi-Club: JSON array of club IDs ---
# Lambda env var example: STRAVA_CLUB_IDS=["1793883","9876543","1234567"]
_raw_club_ids = os.getenv('STRAVA_CLUB_IDS', '[]')
try:
    STRAVA_CLUB_IDS = json.loads(_raw_club_ids)
except json.JSONDecodeError:
    print(f"⚠️ Warning: Could not parse STRAVA_CLUB_IDS='{_raw_club_ids}'. Defaulting to empty list.")
    STRAVA_CLUB_IDS = []

# --- DynamoDB ---
ACTIVITIES_TABLE_NAME = os.getenv('ACTIVITIES_TABLE_NAME', '').strip()
if not ACTIVITIES_TABLE_NAME:
    raise ValueError("Missing environment variable: ACTIVITIES_TABLE_NAME")

ATHLETES_TABLE_NAME = os.getenv('ATHLETES_TABLE_NAME', '').strip()
if not ATHLETES_TABLE_NAME:
    raise ValueError("Missing environment variable: ATHLETES_TABLE_NAME")

AWS_REGION = os.getenv('AWS_REGION', 'eu-west-1')

# --- Constants ---
AUTH_URL = "https://www.strava.com/oauth/token"
ACTIVITIES_URL_TEMPLATE = "https://www.strava.com/api/v3/clubs/{club_id}/activities"