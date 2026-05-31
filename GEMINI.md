# 🌊 ACTIVUM Rides the Wave — AI Agent Context

> This file provides full project context for any AI coding agent working on this
> repository. Read this before making changes.
>
> **This is a fork of the Ride the Wave project**, adapted for multi-club Strava
> tracking with an athlete leaderboard. Key differences from the original:
> - Data source: **Strava Clubs** (not individual athlete) — no polylines, no activity IDs
> - Multiple clubs supported simultaneously
> - Athletes ranking table (`ACTIVUM_USR`)
> - No map/carousel with route data — activity cards are text-only

---

## 1. Project Overview

**ACTIVUM Rides the Wave** is a multi-club Strava activity dashboard that:
1. Fetches activity data from **multiple Strava Clubs** simultaneously
2. Stores activities in **AWS DynamoDB** (`ACTIVUM_ACT`) and athlete rankings (`ACTIVUM_USR`)
3. Displays it on a **premium React dashboard** deployed to Vercel

The dashboard shows:
- **Total km counter** — sum of all club activities (all sport types)
- **Progress bar** toward a configurable `GOAL_KM`
- **Top 10 athletes** ranked by total accumulated km
- **Activity carousel** — last `LAST_ACT` activities, text-only (no maps)

---

## 2. Architecture

```
┌─────────────────┐    Schedule     ┌──────────────────┐
│  Strava Clubs   │◄───────────────│  ActivumCounter  │
│  (Multiple)     │   every 6h     │  Worker (Lambda) │
└─────────────────┘                └──────┬───────────┘
                                          │ write
                                   ┌──────▼────────────────────┐
                                   │   DynamoDB                 │
                                   │   ACTIVUM_ACT (activities) │
                                   │   ACTIVUM_USR (athletes)   │
                                   └──────┬────────────────────-┘
                                          │ read
                                   ┌──────▼───────┐     HTTPS      ┌──────────────┐
                                   │   API        │◄───────────────│   Frontend   │
                                   │  (Lambda)    │  Function URL  │  (Vercel)    │
                                   └──────────────┘                └──────────────┘
```

### Component Details

| Component    | Runtime       | Deployment             | Entry Point                          |
|-------------|---------------|------------------------|--------------------------------------|
| **Worker**  | Python 3.12   | AWS Lambda `ActivumCounterWorker` + EventBridge | `worker/strava_retreiver.py` → `retrieve_strava_data_lambda` |
| **API**     | Python 3.12   | AWS Lambda `StravaCounterBackendAPI` + Function URL | `api/backend_source.py` → `process_activities` |
| **Frontend**| React 19 + Vite 7 | Vercel (auto-deploy on push) | `frontend/src/main.jsx` |
| **DB (activities)** | DynamoDB | AWS (eu-west-1) | Table: `ACTIVUM_ACT` |
| **DB (athletes)** | DynamoDB | AWS (eu-west-1) | Table: `ACTIVUM_USR` |

---

## 3. Directory Structure

```
strava-counter-almas-inquietas/
├── .github/workflows/
│   ├── deploy-api.yaml           # CI/CD: Deploy API Lambda on push (api/** changes)
│   └── deploy-worker.yaml        # CI/CD: Deploy Worker Lambda on push (worker/** changes)
│
├── api/                          # Backend API (Python, AWS Lambda)
│   ├── backend_source.py         # Lambda handler + local Flask server
│   ├── api_config.py             # All env var loading with defaults
│   ├── auth.py                   # HMAC signature verification + Bearer token management
│   ├── rate_limiter.py           # Sliding window rate limiter per IP
│   ├── db.py                     # DynamoDB reads (activities + athletes)
│   ├── services.py               # Business logic: aggregation, ranking
│   ├── utils.py                  # DecimalEncoder, json_response helper
│   └── .env                      # Local dev env vars (NOT deployed, excluded from zip)
│
├── worker/                       # Multi-Club Data Retriever (Python, AWS Lambda)
│   ├── strava_retreiver.py       # Lambda handler — loops over all clubs
│   ├── config.py                 # Env var loading (Strava creds, club IDs, AWS config)
│   ├── strava_client.py          # Strava OAuth token refresh + paginated club activity fetch
│   ├── database.py               # DynamoDB write: save_activity + upsert_athlete
│   ├── requirements.txt          # Python deps (requests, boto3, python-dotenv)
│   └── .env                      # Local dev env vars (NOT deployed)
│
├── frontend/                     # React Dashboard (Vite)
│   ├── index.html                # HTML shell (Google Fonts: Inter + Racing Sans One)
│   ├── vite.config.js            # Vite config (React plugin only)
│   ├── package.json              # Deps: react 19, recharts
│   ├── .env.development          # Local API URL + dev auth keys
│   ├── .env.production           # Production Lambda URL + production auth keys
│   └── src/
│       ├── main.jsx              # React entry (StrictMode)
│       ├── App.jsx               # Root: data fetch, auth, counter, leaderboard, carousel
│       ├── App.css               # Component styles (glassmorphism, animations, cards)
│       ├── index.css             # Design system: CSS custom properties, global reset
│       ├── config.js             # API_URL export, sport type icons/labels
│       ├── apiAuth.js            # HMAC signing + Bearer token caching (sessionStorage)
│       └── components/
│           ├── ActivityCarousel.jsx  # Horizontal scroll carousel of activity cards
│           └── ActivityCard.jsx      # Text-only activity card (no map)
│
├── tests/                        # Unit tests (pytest + moto)
│   ├── conftest.py               # Shared fixtures, mocked DynamoDB tables
│   ├── test_worker/
│   │   ├── test_config.py        # STRAVA_CLUB_IDS parsing tests
│   │   ├── test_database.py      # save_activity + upsert_athlete tests
│   │   └── test_strava_client.py # Auth + fetch tests (mocked HTTP)
│   └── test_api/
│       ├── test_auth.py          # HMAC + token lifecycle tests
│       ├── test_rate_limiter.py  # Sliding window tests
│       ├── test_services.py      # Aggregation + ranking tests
│       └── test_backend_source.py# Lambda routing + CORS tests
│
├── testing_api/                  # Manual exploration scripts (not deployed)
│   ├── api_strava.py             # Interactive Strava API exploration
│   └── actividades_club.csv      # Sample activity data
│
├── .gitignore
└── README.md
```

---

## 4. Tech Stack & Dependencies

### Backend (API + Worker)
- **Language:** Python 3.12
- **AWS SDK:** `boto3` (DynamoDB interactions)
- **HTTP (Worker only):** `requests` (Strava API calls)
- **Local server:** `flask` + `flask-cors` (development only, not deployed)
- **Env loading:** `python-dotenv` (development only)

### Frontend
- **Framework:** React 19.2 with Vite 7.2
- **Charts:** Recharts 3.8 (available, not currently used)
- **Fonts:** Google Fonts — `Inter` (body), `Racing Sans One` (display headings)
- **No maps:** Strava Club API does not provide polylines

### Infrastructure
- **Database:** AWS DynamoDB, eu-west-1
  - `ACTIVUM_ACT` — activities (PK: `activity_id`, synthetic MD5)
  - `ACTIVUM_USR` — athletes (PK: `athlete_name`)
- **Compute:** AWS Lambda (Python 3.12)
- **API Gateway:** Lambda Function URL (supports payload formats v1.0 + v2.0)
- **Frontend Hosting:** Vercel (auto-deploys from `master` branch)
- **CI/CD:** GitHub Actions (path-filtered deploys)

---

## 5. Authentication System

The API uses a **two-step HMAC + Bearer token** authentication flow:

### Step 1 — Token Request (`POST /auth/token`)
```
Headers:
  X-Api-Key:    <API_KEY>
  X-Timestamp:  <unix_epoch_seconds>
  X-Nonce:      <crypto.randomUUID()>
  X-Signature:  HMAC-SHA256(API_SIGNING_SECRET, "{timestamp}.{nonce}")
```

The backend verifies:
1. `X-Api-Key` matches the configured `API_KEY`
2. Timestamp is within `AUTH_TOLERANCE_SECONDS` (default: 300s) of server time
3. HMAC signature is valid

### Step 2 — Data Request (`GET /`)
```
Authorization: Bearer <token>
```
Token validated against in-memory `_active_tokens` dict in `auth.py`. Lazily cleaned up.

### Auth Passthrough Mode
If `API_KEY` or `API_SIGNING_SECRET` are empty → **auth disabled**. Default for local dev.

### Frontend Auth Flow (`apiAuth.js`)
- Tokens cached in `sessionStorage` with 30s safety buffer
- No auth headers sent if `VITE_API_KEY`/`VITE_API_SIGNING_SECRET` are empty
- Uses Web Crypto API (no external libs)

---

## 6. API Response Contract

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

### Key Fields
- `total_km` — sum of ALL activities, ALL sport types (no filter)
- `top_athletes` — max 10, sorted by `currentKm` descending
- `top_athletes[].lastIncrement` — km from the most recently processed new activity
- `last_activities` — most recent `LAST_ACT` activities, newest-first
- No `summary_polyline`, `kudos_count`, `pace` — not available from Club API

---

## 7. Design System & UI Conventions

### Color Palette
| Token                    | Value      | Usage                       |
|--------------------------|------------|-----------------------------|
| `--activum-teal`         | `#62c0bb`  | Primary accent color        |
| `--activum-teal-light`   | `#82d0cc`  | Progress bar gradient end   |
| `--activum-teal-dark`    | `#43aaa4`  | Progress bar gradient start |
| `--bg-primary`           | `#f0f4f8`  | Page background             |
| `--bg-card`              | `rgba(255,255,255,0.82)` | Glassmorphism cards |
| `--text-primary`         | `#0f172a`  | Headings, main text         |
| `--text-secondary`       | `#475569`  | Body copy                   |
| `--text-muted`           | `#94a3b8`  | Labels, captions            |

### Sport Icons (config.js)
| Sport      | Icon | Label      |
|------------|------|------------|
| Run        | 🏃   | Carrera    |
| Ride       | 🚴   | Ciclismo   |
| Swim       | 🏊   | Natación   |
| Hike       | 🥾   | Senderismo |
| Walk       | 🚶   | Caminata   |
| Workout    | 💪   | Entreno    |
| VirtualRun | 🖥️   | Virtual    |
| Default    | ⚡   | Actividad  |

### UI Patterns
- **Glassmorphism:** `rgba(255,255,255,0.82)` + `backdrop-filter: blur(12px)` + border/shadow
- **Border Radii:** `--radius-sm: 8px`, `--radius-md: 14px`, `--radius-lg: 20px`
- **Animations:** `fadeInUp` with `.stagger` delays, `shimmer` on progress bar, `countUp` on number
- **Medals:** Top 3 athletes show 🥇🥈🥉 badges; rows 4-10 show numeric rank
- **Fonts:** `Racing Sans One` for headings, `Inter` for body
- **Layout:** `#root` 90% width, max 960px centered. Mobile breakpoint at 768px
- **Language:** Spanish UI labels ("Kilómetros recorridos", "Ranking de atletas", etc.)

---

## 8. Worker — Multi-Club Logic

The worker fetches from all clubs configured in `STRAVA_CLUB_IDS` using a **single OAuth token** (same Strava API app handles all clubs).

### Key Behaviors
- Only saves **new** activities (conditional `attribute_not_exists(activity_id)` put)
- Only calls `upsert_athlete()` when `save_activity()` returns `True` → no double-counting
- Generates synthetic MD5 IDs from `Athlete + Name + Distance + MovingTime + ElapsedTime + Type`
- `start_date` defaults to `datetime.utcnow()` when not provided by the Club API

### Club API Data Available
```json
{
  "athlete": { "firstname": "Daniel", "lastname": "F." },
  "name": "Morning Run",
  "distance": 10026.2,
  "moving_time": 3643,
  "elapsed_time": 3838,
  "total_elevation_gain": 113.4,
  "type": "Run",
  "sport_type": "Run"
}
```
**No:** `id`, `start_date`, `summary_polyline`, `kudos_count`, `average_speed`

---

## 9. DynamoDB Schema

### `ACTIVUM_ACT` — Activities
**Partition Key:** `activity_id` (String)

| Field | Type | Description |
|-------|------|-------------|
| `activity_id` | String (PK) | Synthetic MD5 ID |
| `title` | String | Activity name |
| `type` | String | Sport type (Run, Ride, etc.) |
| `sport_type` | String | Same as type (from API) |
| `athlete` | String | `"Firstname Lastname"` |
| `distance_km` | Number | Distance in km |
| `moving_time_seconds` | Number | Moving time |
| `total_elevation_gain` | Number | Elevation in meters |
| `start_date` | String | ISO 8601 UTC (defaulted to utcnow) |

### `ACTIVUM_USR` — Athletes
**Partition Key:** `athlete_name` (String)

| Field | Type | Description |
|-------|------|-------------|
| `athlete_name` | String (PK) | `"Firstname Lastname"` |
| `currentKm` | Number | Total accumulated km (atomic ADD) |
| `lastIncrement` | Number | Most recent new activity's km |

> **Known limitation:** Athlete names from the Club API are abbreviated (e.g., "Daniel F."). Name collisions are possible but accepted.

---

## 10. Environment Variables

### Worker Lambda (`ActivumCounterWorker`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `STRAVA_CLIENT_ID` | Yes | — | Strava OAuth client ID |
| `STRAVA_CLIENT_SECRET` | Yes | — | Strava OAuth client secret |
| `STRAVA_REFRESH_TOKEN` | Yes | — | Long-lived refresh token |
| `STRAVA_CLUB_IDS` | Yes | `[]` | JSON array, e.g. `["1793883","9876543"]` |
| `ACTIVITIES_TABLE_NAME` | No | `ACTIVUM_ACT` | Activities table |
| `ATHLETES_TABLE_NAME` | No | `ACTIVUM_USR` | Athletes table |
| `AWS_REGION` | No | `eu-west-1` | AWS region |

### API Lambda (`StravaCounterBackendAPI`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ACTIVITIES_TABLE_NAME` | No | `ACTIVUM_ACT` | Activities table |
| `ATHLETES_TABLE_NAME` | No | `ACTIVUM_USR` | Athletes table |
| `AWS_REGION` | No | `eu-west-1` | AWS region |
| `GOAL_KM` | No | `500` | Target km for progress bar |
| `LAST_ACT` | No | `10` | Number of recent activities to return |
| `API_KEY` | No* | `''` | API key for HMAC auth |
| `API_SIGNING_SECRET` | No* | `''` | HMAC signing secret |
| `AUTH_TOLERANCE_SECONDS` | No | `300` | Max clock skew |
| `TOKEN_TTL_SECONDS` | No | `300` | Bearer token lifetime |
| `RATE_LIMIT_MAX` | No | `30` | Max requests per window |
| `RATE_LIMIT_WINDOW` | No | `60` | Rate limit window (seconds) |
| `CORS_ALLOWED_ORIGINS` | No | `http://localhost:5173,...` | Allowed CORS origins |

> \*If empty, auth is disabled (passthrough mode).

### Frontend (`VITE_*`)

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | Yes | Backend Lambda Function URL |
| `VITE_API_KEY` | No* | Must match backend `API_KEY` |
| `VITE_API_SIGNING_SECRET` | No* | Must match backend secret |

---

## 11. CI/CD & Deployment

### GitHub Actions

#### `deploy-api.yaml` — API Lambda
- **Triggers:** Push to `master` when `api/**` changes
- **Steps:** Checkout → Python 3.12 → Zip `api/` (excluding `.env`) → Deploy to `StravaCounterBackendAPI`

#### `deploy-worker.yaml` — Worker Lambda
- **Triggers:** Push to `master` when `worker/**` changes
- **Steps:** Checkout → Python 3.12 → `pip install -r requirements.txt -t .` → Zip (excluding `.env`) → Deploy to `ActivumCounterWorker`

> ⚠️ **CRITICAL:** `.env` files are excluded from Lambda zips. All Lambda env vars must be set in the **AWS Lambda console**.

### Frontend (Vercel)
- Auto-deploys from `master` branch
- Set `VITE_*` env vars in Vercel project settings

---

## 12. Local Development

### Startup Sequence

```bash
# 1. Start the backend API
cd api
pip install flask flask-cors boto3 python-dotenv
python backend_source.py
# → http://127.0.0.1:5000

# 2. Start the frontend
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### Local Auth
`api/.env` and `frontend/.env.development` use matching dev keys:
- `API_KEY=dev-local-key-12345`
- `API_SIGNING_SECRET=dev-local-secret-abcdef0123456789`

### Running Tests
```bash
pip install pytest moto boto3 requests python-dotenv
pytest tests/ -v
```

---

## 13. Known Gotchas & Common Pitfalls

### Lambda Payload Format
Handler supports both v1.0 and v2.0 Function URL formats:
- Path: `event.rawPath` (v2.0) or `event.path` (v1.0)
- Method: `event.requestContext.http.method` (v2.0) or `event.httpMethod` (v1.0)
- Client IP: `event.requestContext.http.sourceIp` (v2.0) or `event.requestContext.identity.sourceIp` (v1.0)

### In-Memory State (Lambda Cold Starts)
`_active_tokens` and `_request_history` reset on cold starts. Acceptable for low-traffic use.

### CORS
- CORS headers added to **every response** (including errors and 4xx)
- Origin whitelisted from `CORS_ALLOWED_ORIGINS`

### Worker — No Polylines
Strava Club API never returns `summary_polyline`. Do not attempt to save or display routes.

### Worker — Synthetic IDs
MD5 hash of activity properties. Changing the hashing fields will cause all existing activities to appear as new on the next run.

### Frontend `.env` Files ARE Committed to Git
`frontend/.env.*` are tracked. Never commit real production secrets.

---

## 14. Branching & Workflow Conventions

- **`master`** is the production branch. All merges go here.
- Feature branches: `feature/<descriptive-name>`
- Keep `api/`, `worker/`, `frontend/` changes in separate commits to avoid unnecessary Lambda deploys

---

## 15. AWS Resources Required

| Resource | Details |
|----------|---------|
| DynamoDB `ACTIVUM_ACT` | PK: `activity_id` (String), eu-west-1 |
| DynamoDB `ACTIVUM_USR` | PK: `athlete_name` (String), eu-west-1 |
| Lambda `ActivumCounterWorker` | Python 3.12, handler: `strava_retreiver.retrieve_strava_data_lambda` |
| Lambda `StravaCounterBackendAPI` | Python 3.12, handler: `backend_source.process_activities`, Function URL |
| EventBridge Rule | Trigger `ActivumCounterWorker` on schedule (e.g., every 6h) |
| IAM Role (Worker) | DynamoDB PutItem on `ACTIVUM_ACT` + UpdateItem on `ACTIVUM_USR` |
| IAM Role (API) | DynamoDB Scan on `ACTIVUM_ACT` + Scan on `ACTIVUM_USR` |
