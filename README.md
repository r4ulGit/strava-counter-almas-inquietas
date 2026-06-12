# 🌊 Rides the Wave

Multi-club Strava activity dashboard that aggregates activities from multiple Strava Clubs, tracks athlete rankings, and displays real-time progress toward a configurable goal.

---

## ✨ Features

- **Total KM Counter** — Sum of all (optionally filtered) club activities
- **Progress Bar** — Animated progress toward a configurable `GOAL_KM` (hidden when not set)
- **Top 10 Athlete Leaderboard** — Ranked by total accumulated km with medal badges
- **Activity Carousel** — Horizontally scrollable cards showing the most recent activities
- **Multi-Club Support** — Fetch and merge activities from multiple Strava Clubs simultaneously
- **Activity Filtering** — Server-side filtering by sport type, activity title, and start date
- **Embeddable Views** — `?view=counter|ranking|activities` query param for single-section embeds
- **HMAC Authentication** — Two-step token-based auth with configurable passthrough mode
- **Rate Limiting** — Sliding window per-IP rate limiter
- **Glassmorphism UI** — Premium design with animations, blur effects, and responsive layout

---

## 🏗️ Architecture

```
┌─────────────────┐    Schedule     ┌──────────────────┐
│  Strava Clubs   │◄───────────────│  Strava Counter  │
│  (Multiple)     │   every 6h     │  Worker (Lambda) │
└─────────────────┘                └──────┬───────────┘
                                          │ write
                                   ┌──────▼────────────────────┐
                                   │   DynamoDB                 │
                                   │   Activities table          │
                                   │   Athletes table            │
                                   └──────┬─────────────────────┘
                                          │ read
                                   ┌──────▼───────┐     HTTPS      ┌──────────────┐
                                   │   API        │◄───────────────│   Frontend   │
                                   │  (Lambda)    │  Function URL  │  (Vercel)    │
                                   └──────────────┘                └──────────────┘
```

| Component      | Runtime         | Deployment                                           |
|----------------|-----------------|------------------------------------------------------|
| **Worker**     | Python 3.12     | AWS Lambda + EventBridge (6h schedule)                |
| **API**        | Python 3.12     | AWS Lambda + Function URL                             |
| **Frontend**   | React 19 + Vite 7 | Vercel (auto-deploy on `master` push)              |
| **Database**   | DynamoDB        | AWS — configurable table names via env vars           |

---

## 📁 Project Structure

```
strava-counter-almas-inquietas/
├── .github/workflows/
│   ├── deploy-api.yaml            # CI/CD: Deploy API Lambda (matrix strategy per environment)
│   └── deploy-worker.yaml         # CI/CD: Deploy Worker Lambda (matrix strategy per environment)
│
├── api/                           # Backend API (Python, AWS Lambda)
│   ├── backend_source.py          # Lambda handler + local Flask dev server
│   ├── api_config.py              # All env var loading with defaults
│   ├── auth.py                    # HMAC signature verification + Bearer token management
│   ├── rate_limiter.py            # Sliding window rate limiter per IP
│   ├── db.py                      # DynamoDB reads (activities + athletes)
│   ├── services.py                # Business logic: aggregation, filtering, ranking
│   ├── utils.py                   # DecimalEncoder, json_response helper
│   └── .env                       # Local dev env vars (excluded from Lambda deploys)
│
├── worker/                        # Multi-Club Data Retriever (Python, AWS Lambda)
│   ├── strava_retreiver.py        # Lambda handler — loops over all clubs
│   ├── config.py                  # Env var loading (Strava creds, club IDs, AWS config)
│   ├── strava_client.py           # Strava OAuth token refresh + paginated club activity fetch
│   ├── database.py                # DynamoDB write: save_activity + upsert_athlete
│   └── requirements.txt           # Python deps (requests, boto3, python-dotenv)
│
├── frontend/                      # React Dashboard (Vite)
│   ├── index.html                 # HTML shell (Google Fonts: Inter + Racing Sans One)
│   ├── vite.config.js             # Vite config (React plugin)
│   ├── package.json               # Deps: react 19, recharts
│   ├── .env.development           # Local API URL + dev auth keys
│   ├── .env.production            # Production Lambda URL + production auth keys
│   └── src/
│       ├── main.jsx               # React entry (StrictMode)
│       ├── App.jsx                # Root: data fetch, auth, counter, leaderboard, carousel
│       ├── App.css                # Component styles (glassmorphism, animations, cards)
│       ├── index.css              # Design system: CSS custom properties, global reset
│       ├── config.js              # API_URL export, sport type icons/labels
│       ├── apiAuth.js             # HMAC signing + Bearer token caching (sessionStorage)
│       └── components/
│           ├── ActivityCarousel.jsx  # Horizontal scroll carousel of activity cards
│           └── ActivityCard.jsx      # Text-only activity card (no map)
│
├── tests/                         # Unit tests (pytest + moto)
│   ├── conftest.py                # Shared fixtures, mocked DynamoDB tables
│   ├── test_worker/               # Worker tests (config parsing, DB writes, HTTP mocks)
│   └── test_api/                  # API tests (auth, rate limiting, services, routing)
│
├── testing_api/                   # Manual exploration scripts (not deployed)
│   ├── api_strava.py              # Interactive Strava API exploration
│   └── actividades_club.csv       # Sample activity data
│
├── GEMINI.md                      # AI agent context file
└── README.md                      # ← You are here
```

---

## ⚙️ Environment Variables

### Worker Lambda

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `STRAVA_CLIENT_ID` | ✅ | — | Strava OAuth client ID |
| `STRAVA_CLIENT_SECRET` | ✅ | — | Strava OAuth client secret |
| `STRAVA_REFRESH_TOKEN` | ✅ | — | Long-lived Strava refresh token |
| `STRAVA_CLUB_IDS` | ✅ | `[]` | JSON array of club IDs, e.g. `["123456","789012"]` |
| `ACTIVITIES_TABLE_NAME` | ✅ | — | DynamoDB activities table name |
| `ATHLETES_TABLE_NAME` | ✅ | — | DynamoDB athletes table name |
| `AWS_REGION` | ❌ | `eu-west-1` | AWS region for DynamoDB |

### API Lambda

#### Core Configuration

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `ACTIVITIES_TABLE_NAME` | ✅ | — | DynamoDB activities table name |
| `ATHLETES_TABLE_NAME` | ✅ | — | DynamoDB athletes table name |
| `AWS_REGION` | ❌ | `eu-west-1` | AWS region for DynamoDB |
| `GOAL_KM` | ❌ | *none* | Target km for the progress bar. If empty or unset, the progress bar is hidden and only the total km counter is shown |
| `LAST_ACT` | ❌ | `10` | Number of recent activities to return in the carousel |

#### Activity Filtering

These variables filter the activities **at response time** (API-level), without modifying the underlying database. When a filter is active, the total km counter and athlete leaderboard are dynamically recalculated to match only the filtered activities.

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `ACT_TYPE_FILTER` | ❌ | *none* | Comma-separated list of sport types to include, e.g. `Run,Ride,Swim`. If empty or unset, all types are returned |
| `ACT_TITLE_FILTER` | ❌ | *none* | Substring filter on activity titles (case-insensitive). If empty or unset, all titles are returned |
| `START_DATE` | ❌ | *none* | ISO 8601 date string, e.g. `2026-06-01T00:00:00Z`. Activities before this date are excluded. If empty or unset, no date filter is applied |

#### Authentication

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `API_KEY` | ❌* | `''` | API key for HMAC authentication |
| `API_SIGNING_SECRET` | ❌* | `''` | HMAC-SHA256 signing secret |
| `AUTH_TOLERANCE_SECONDS` | ❌ | `300` | Max clock skew tolerance for timestamp validation |
| `TOKEN_TTL_SECONDS` | ❌ | `300` | Bearer token lifetime in seconds |

> \* If `API_KEY` or `API_SIGNING_SECRET` are empty, auth is **disabled** (passthrough mode).

#### Rate Limiting

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `RATE_LIMIT_MAX` | ❌ | `30` | Max requests allowed per window per IP |
| `RATE_LIMIT_WINDOW` | ❌ | `60` | Rate limit window in seconds |

#### CORS

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `CORS_ALLOWED_ORIGINS` | ❌ | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated list of allowed origins |

### Frontend (Vite `VITE_*`)

| Variable | Required | Description |
|----------|:--------:|-------------|
| `VITE_API_URL` | ✅ | Backend Lambda Function URL |
| `VITE_API_KEY` | ❌* | Must match backend `API_KEY` |
| `VITE_API_SIGNING_SECRET` | ❌* | Must match backend `API_SIGNING_SECRET` |

> \* If empty, the frontend skips the auth handshake.

---

## 🔐 Authentication Flow

The API uses a **two-step HMAC + Bearer token** flow:

### 1. Token Request — `POST /auth/token`

```
Headers:
  X-Api-Key:    <API_KEY>
  X-Timestamp:  <unix_epoch_seconds>
  X-Nonce:      <crypto.randomUUID()>
  X-Signature:  HMAC-SHA256(API_SIGNING_SECRET, "{timestamp}.{nonce}")
```

### 2. Data Request — `GET /`

```
Authorization: Bearer <token>
```

> **Passthrough mode:** If `API_KEY` or `API_SIGNING_SECRET` are empty on both backend and frontend, authentication is completely bypassed.

---

## 📡 API Response

`GET /` returns:

```json
{
  "total_km": 1234.56,
  "total_activities": 45,
  "top_athletes": [
    {
      "athlete_name": "Daniel F.",
      "currentKm": 123.45,
      "lastIncrement": 10.50
    }
  ],
  "last_activities": [
    {
      "id": "a1b2c3d4...",
      "title": "Morning Run",
      "athlete": "Daniel F.",
      "type": "Run",
      "sport_type": "Run",
      "distance_km": 10.03,
      "moving_time_seconds": 3643,
      "date": "2026-05-30T08:15:00Z"
    }
  ],
  "config": {
    "goal_km": 12000
  }
}
```

---

## 🗄️ DynamoDB Schema

### Activities Table (`ACTIVITIES_TABLE_NAME`)

| Field | Type | Description |
|-------|------|-------------|
| `activity_id` (PK) | String | Synthetic MD5 hash |
| `title` | String | Activity name |
| `type` / `sport_type` | String | Sport type (Run, Ride, Swim, etc.) |
| `athlete` | String | `"Firstname Lastname"` |
| `distance_km` | Number | Distance in km |
| `moving_time_seconds` | Number | Moving time |
| `total_elevation_gain` | Number | Elevation in meters |
| `start_date` | String | ISO 8601 UTC |

### Athletes Table (`ATHLETES_TABLE_NAME`)

| Field | Type | Description |
|-------|------|-------------|
| `athlete_name` (PK) | String | `"Firstname Lastname"` |
| `currentKm` | Number | Total accumulated km (atomic ADD) |
| `lastIncrement` | Number | Most recent activity's km |

---

## 🚀 CI/CD & Deployment

### GitHub Actions

Both workflows use a **matrix strategy** to deploy to multiple environments simultaneously (one per configured GitHub environment).

| Workflow | Triggers | Lambda Function |
|----------|----------|-----------------|
| `deploy-api.yaml` | Push to `master` when `api/**` changes | `${{ vars.LAMBDA_FUNCTION_API }}` |
| `deploy-worker.yaml` | Push to `master` when `worker/**` changes | `${{ vars.LAMBDA_FUNCTION_WORKER }}` |

Both support `workflow_dispatch` for manual triggers.

> ⚠️ `.env` files are excluded from Lambda zips. All Lambda env vars must be set in the **AWS Lambda console**.

### Frontend (Vercel)

- Auto-deploys from `master` branch
- `VITE_*` env vars must be set in the Vercel project settings
- Each Vercel project points to a different backend Lambda via `VITE_API_URL`

### GitHub Environments

Each GitHub environment requires these secrets/variables:

| Type | Name | Description |
|------|------|-------------|
| Secret | `AWS_ACCESS_KEY_ID` | IAM access key |
| Secret | `AWS_SECRET_ACCESS_KEY` | IAM secret key |
| Variable | `AWS_REGION` | AWS region (e.g. `eu-west-1`) |
| Variable | `LAMBDA_FUNCTION_API` | API Lambda function name |
| Variable | `LAMBDA_FUNCTION_WORKER` | Worker Lambda function name |

---

## 🛠️ Local Development

### Prerequisites

- Python 3.12+
- Node.js 18+
- AWS credentials configured (for DynamoDB access)

### 1. Start the Backend API

```bash
cd api
pip install flask flask-cors boto3 python-dotenv
python backend_source.py
# → http://127.0.0.1:5000
```

### 2. Start the Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### Local Auth

`api/.env` and `frontend/.env.development` use matching dev keys by default:

```env
API_KEY=dev-local-key-12345
API_SIGNING_SECRET=dev-local-secret-abcdef0123456789
```

### Running Tests

```bash
pip install pytest moto boto3 requests python-dotenv
pytest tests/ -v
```

---

## 📌 Query Param Views

Append `?view=` to the frontend URL to show a single section:

| URL Param | Shows |
|-----------|-------|
| `?view=counter` | KM counter + progress bar only |
| `?view=ranking` | Athlete leaderboard only |
| `?view=activities` | Activity carousel only |
| *(none)* | Full dashboard (all sections) |

Useful for embedding individual sections in other pages or displays.

---

## ⚠️ Known Limitations

- **No route maps** — Strava Club API does not provide `summary_polyline`
- **No activity IDs from Strava** — Synthetic MD5 IDs are generated from activity properties
- **Abbreviated athlete names** — Club API abbreviates last names (e.g. "John D.") — name collisions are possible
- **In-memory auth state** — `_active_tokens` reset on Lambda cold starts (acceptable for low traffic)
- **DynamoDB Scan** — Full table scans on every API request; adequate for moderate data volumes

---

## 📝 Branching Convention

- **`master`** — Production branch (auto-deploys)
- Feature branches: `feature/<descriptive-name>`
- Keep `api/`, `worker/`, `frontend/` changes in separate commits to avoid unnecessary Lambda deploys