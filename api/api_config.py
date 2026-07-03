import os
from pathlib import Path

# Load environment variables (for local testing)
try:
    from dotenv import load_dotenv
    current_dir = Path(__file__).resolve().parent
    load_dotenv(dotenv_path=current_dir / '.env')
except ImportError:
    # python-dotenv is not installed in the AWS Lambda runtime, which is expected.
    # Environment variables are loaded directly from the Lambda console.
    pass

# --- DynamoDB ---
ACTIVITIES_TABLE_NAME = os.getenv('ACTIVITIES_TABLE_NAME', '').strip()
if not ACTIVITIES_TABLE_NAME:
    raise ValueError("Missing environment variable: ACTIVITIES_TABLE_NAME")

ATHLETES_TABLE_NAME = os.getenv('ATHLETES_TABLE_NAME', '').strip()
if not ATHLETES_TABLE_NAME:
    raise ValueError("Missing environment variable: ATHLETES_TABLE_NAME")

AWS_REGION = os.getenv('AWS_REGION', 'eu-west-1')

# --- App Config ---
# GOAL_KM is None when the env var is not set or is empty.
# The frontend hides the progress bar when goal_km is null.
_goal_km_raw = os.getenv('GOAL_KM', '').strip()
if _goal_km_raw:
    try:
        GOAL_KM = float(_goal_km_raw)
    except (ValueError, TypeError):
        GOAL_KM = None
else:
    GOAL_KM = None

# --- Checkpoints ---
# Comma-separated km values for progress bar milestones.
# Only effective when GOAL_KM is set. Example: "500,1000,2000,5000"
_checkpoints_raw = os.getenv('CHECKPOINTS', '').strip()
if _checkpoints_raw and GOAL_KM is not None:
    CHECKPOINTS = []
    for val in _checkpoints_raw.split(','):
        val = val.strip()
        if val:
            try:
                CHECKPOINTS.append(float(val))
            except (ValueError, TypeError):
                pass
    CHECKPOINTS.sort()
else:
    CHECKPOINTS = []


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

# --- Activity Filtering ---
_act_type_filter_raw = os.getenv('ACT_TYPE_FILTER', '').strip()
if _act_type_filter_raw:
    ACT_TYPE_FILTER = [t.strip() for t in _act_type_filter_raw.split(',') if t.strip()]
else:
    ACT_TYPE_FILTER = []

ACT_TITLE_FILTER = os.getenv('ACT_TITLE_FILTER', '').strip()
START_DATE = os.getenv('START_DATE', '').strip()

# --- Title Config ---
TITLE = os.getenv('TITLE', 'Rides the Wave').strip()
