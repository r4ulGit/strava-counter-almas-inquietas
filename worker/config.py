import os
from dotenv import load_dotenv

# Load environment variables (for local testing)
load_dotenv()

# --- ENVIRONMENT VARIABLES ---
STRAVA_CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
STRAVA_CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
STRAVA_REFRESH_TOKEN = os.getenv('STRAVA_REFRESH_TOKEN')
STRAVA_CLUB_ID = os.getenv('STRAVA_CLUB_ID')
DYNAMODB_TABLE_NAME = os.getenv('DYNAMODB_TABLE_NAME', 'strava_activities')
AWS_REGION = os.getenv('AWS_REGION', 'eu-west-1')

# --- CONSTANTS & URLS ---
AUTH_URL = "https://www.strava.com/oauth/token"

# Construct URL safely to avoid import errors if env var is missing during build
_club_id_safe = STRAVA_CLUB_ID if STRAVA_CLUB_ID else "UNKNOWN_CLUB_ID"
ACTIVITIES_URL = f"https://www.strava.com/api/v3/clubs/{_club_id_safe}/activities"