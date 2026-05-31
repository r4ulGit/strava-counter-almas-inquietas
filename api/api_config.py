import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables (for local testing)
current_dir = Path(__file__).resolve().parent
load_dotenv(dotenv_path=current_dir / '.env')

# --- DynamoDB ---
ACTIVITIES_TABLE_NAME = os.getenv('ACTIVITIES_TABLE_NAME', 'ACTIVUM_ACT')
ATHLETES_TABLE_NAME = os.getenv('ATHLETES_TABLE_NAME', 'ACTIVUM_USR')
AWS_REGION = os.getenv('AWS_REGION', 'eu-west-1')

# --- App Config ---
try:
    GOAL_KM = float(os.getenv('GOAL_KM', 500))
except (ValueError, TypeError):
    GOAL_KM = 500.0

try:
    LAST_ACT = int(os.getenv('LAST_ACT', 10))
except (ValueError, TypeError):
    LAST_ACT = 10

# --- Authentication ---
# If API_KEY or API_SIGNING_SECRET are empty, auth is DISABLED (passthrough mode).
API_KEY = os.getenv('API_KEY', '')
API_SIGNING_SECRET = os.getenv('API_SIGNING_SECRET', '')

try:
    AUTH_TOLERANCE_SECONDS = int(os.getenv('AUTH_TOLERANCE_SECONDS', 300))
except (ValueError, TypeError):
    AUTH_TOLERANCE_SECONDS = 300

try:
    TOKEN_TTL_SECONDS = int(os.getenv('TOKEN_TTL_SECONDS', 300))
except (ValueError, TypeError):
    TOKEN_TTL_SECONDS = 300

# --- Rate Limiting ---
try:
    RATE_LIMIT_MAX = int(os.getenv('RATE_LIMIT_MAX', 30))
except (ValueError, TypeError):
    RATE_LIMIT_MAX = 30

try:
    RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', 60))
except (ValueError, TypeError):
    RATE_LIMIT_WINDOW = 60

# --- CORS ---
CORS_ALLOWED_ORIGINS = os.getenv(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:5173,http://127.0.0.1:5173'
)
