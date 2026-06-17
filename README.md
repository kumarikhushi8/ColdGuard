# ❄️ ColdGuard — Cold Chain Intelligence Platform

Real-time spoilage risk monitoring for Indian agricultural cold storage.  
Sensor data → ML risk scoring → mandi price advisory → multilingual farmer alerts via WhatsApp & SMS.

### 🌐 Live Demo

| Service       | URL                                              |
|---------------|--------------------------------------------------|
| Dashboard     | https://coldguard-ui.onrender.com                |
| API (Swagger) | https://coldguard-api.onrender.com/docs          |
| Health Check  | https://coldguard-api.onrender.com/health        |

**Login:** `admin@coldguard.in` / `Admin@123`

> ⚠️ Render free tier — first request may take ~30s to cold-start.

---

## Run Locally

```bash
# 1. Clone & enter project
cd coldguard

# 2. Copy and configure environment (optional — works without it)
cp .env.example .env
# Edit .env to add: ANTHROPIC_API_KEY, WHATSAPP_TOKEN, SMS_API_KEY, GOOGLE_CLIENT_ID

# 3. Start everything
./start.sh
# Or manually: docker compose up --build
```

| Service       | URL                          |
|---------------|------------------------------|
| Dashboard     | http://localhost:5173         |
| API (Swagger) | http://localhost:8000/docs    |
| PostgreSQL    | localhost:5432                |

---

## Architecture

```
coldguard/
├── backend/
│   └── app/
│       ├── main.py                    # FastAPI entry, lifespan, migrations, background tasks
│       ├── core/
│       │   ├── config.py              # Pydantic settings from env vars
│       │   ├── database.py            # asyncpg pool with retry logic
│       │   ├── auth.py                # JWT creation/verify, bcrypt, OTP generation
│       │   └── dependencies.py        # RBAC guards: require_admin, require_operator
│       ├── api/
│       │   ├── auth.py                # Register, login, OTP, Google OAuth, token refresh
│       │   ├── users.py               # User CRUD, facility assignment (admin-only)
│       │   ├── dashboard.py           # Summary, facility trend, state filter
│       │   ├── facilities.py          # List / get facilities
│       │   ├── sensors.py             # List sensors, latest reading
│       │   ├── readings.py            # Recent readings per facility
│       │   ├── alerts.py              # List / acknowledge alerts
│       │   ├── notifications.py       # WhatsApp/SMS config, test, manual alert
│       │   ├── mandi.py               # Prices, advisory per facility
│       │   └── analytics.py           # ROI, loss prevented, excursions, CSV export
│       ├── ml/
│       │   └── risk_engine.py         # 4-factor spoilage risk model (0–1 score)
│       └── services/
│           ├── simulator.py           # National sensor data generator (10 states)
│           ├── alert_service.py       # Alert creation + Claude translation (HI/MR)
│           ├── notification_service.py # WhatsApp (Meta API) + SMS (fast2sms)
│           ├── advisory_engine.py     # Sell/hold/move decisions (risk + price)
│           ├── analytics_engine.py    # ICAR-based loss prevention & ROI metrics
│           └── mandi_service.py       # Market price fetcher (50 mandis × 20 crops)
├── frontend/
│   └── src/
│       ├── App.jsx                    # Routes, ProtectedRoute, AuthCallback
│       ├── context/AuthContext.jsx     # Auth state, JWT storage, auto-refresh on 401
│       ├── pages/
│       │   ├── LoginPage.jsx          # Email/OTP/Google OAuth login
│       │   ├── DashboardPage.jsx      # KPIs, state filter, facility cards, alerts
│       │   ├── FacilityPage.jsx       # Sensor metrics, trend chart, risk gauge
│       │   ├── AlertsPage.jsx         # Active/acknowledged alerts, severity pills
│       │   ├── MandiPage.jsx          # Advisory cards, price ticker, language toggle
│       │   ├── AnalyticsPage.jsx      # ROI charts, loss prevented, CSV export
│       │   ├── NotificationsPage.jsx  # WhatsApp/SMS config, test messages
│       │   └── UsersPage.jsx          # Admin user management
│       ├── components/
│       │   ├── Layout.jsx             # Collapsible sidebar, role-filtered navigation
│       │   ├── dashboard/             # StatCard, FacilityCard, RiskGauge
│       │   ├── alerts/                # AlertItem (expandable, multilingual)
│       │   └── sensors/               # TrendChart (temp + RH + risk)
│       ├── hooks/usePolling.js        # Generic auto-refresh hook
│       └── lib/
│           ├── api.js                 # API client
│           └── utils.js               # Formatters (temp, RH, ethylene, risk, time)
├── infra/
│   ├── init.sql                       # TimescaleDB schema + seed data (3 facilities)
│   ├── init_render.sql                # Standard PostgreSQL schema (Render deploy)
│   └── expand_facilities.sql          # National expansion: 9 states × 5 facilities
├── docker-compose.yml                 # 4 services: db, backend, simulator, frontend
├── render.yaml                        # Render blueprint (IaC for production)
├── .env.example                       # All env vars with setup instructions
└── start.sh                           # One-command bootstrap with Docker
```

---

## Authentication

Three login flows for three user personas:

| Role     | Login Method             | Access Level                     |
|----------|--------------------------|----------------------------------|
| Admin    | Email + Password         | Full access, user management     |
|          | Google OAuth (optional)  |                                  |
| Operator | Email + Password         | Assigned facilities, analytics   |
| Farmer   | Phone OTP (SMS)          | Own facilities only              |

- **JWT tokens** (HS256): 60-min access + 30-day refresh with rotation
- **RBAC**: `require_admin`, `require_operator`, `require_any` guards on API routes

---

## How the Risk Engine Works

File: `backend/app/ml/risk_engine.py`

Computes a 0–1 spoilage risk score using 4 weighted factors:

| Factor                    | Weight | Source                      |
|---------------------------|--------|-----------------------------|
| Temperature deviation      | 40%    | ICAR post-harvest research  |
| Excursion duration         | 25%    | Time above safe threshold   |
| Relative humidity          | 20%    | Crop-specific RH profiles   |
| Ethylene concentration     | 15%    | Ripening gas ppm            |

Output passes through a sigmoid function for smooth 0→1 transitions.  
Risk levels: `low` < 0.3 < `medium` < 0.6 < `high` < 0.8 < `critical`

### Crop Profiles

| Crop    | Optimal Temp | Optimal RH | Ethylene Threshold | Shelf Life |
|---------|-------------|------------|-------------------|------------|
| Tomato  | 12–15°C     | 85–90%     | 2.0 ppm           | 14 days    |
| Potato  | 4–8°C       | 90–95%     | 0.5 ppm           | 120 days   |
| Onion   | 0–2°C       | 65–70%     | 5.0 ppm           | 180 days   |
| Grapes  | -1–0°C      | 85–90%     | 0.1 ppm           | 28 days    |
| Mango   | 12–13°C     | 85–90%     | 1.0 ppm           | 21 days    |
| Banana  | 13–14°C     | 85–90%     | 0.5 ppm           | 14 days    |

---

## Mandi Advisory Engine

Combines spoilage risk with live market prices to generate actionable advice:

| Condition                          | Action        |
|------------------------------------|---------------|
| Risk ≥ 0.8 + price rising         | 🔴 **SELL NOW**  |
| Risk ≥ 0.8 + price stable/falling | 🚨 **MOVE CROP** |
| Risk ≥ 0.5 + price rising         | 🟡 **SELL SOON** |
| Risk < 0.5                        | 🟢 **HOLD**      |

Explanations are generated in English, Hindi, and Marathi.

---

## Notifications

### WhatsApp (Meta Business API)
- Template-based messages via Graph API v21.0
- Requires `WHATSAPP_TOKEN` + `WHATSAPP_PHONE_ID`

### SMS (fast2sms)
- Free tier: 500 SMS/day
- Requires `SMS_API_KEY`

Both channels have **cooldown tracking** (configurable, default 30 min) to prevent alert fatigue.  
WhatsApp is tried first; SMS is the fallback.

> Without credentials, the system runs in **mock mode** — alerts are logged but not sent.

---

## Alert Translation

If `ANTHROPIC_API_KEY` is set, every alert is translated into Hindi and Marathi  
via Claude API (`claude-sonnet-4-6`). Farmers receive alerts in their language.

Without the key, alerts remain in English only — the system still functions.

---

## Analytics & ROI

Based on ICAR's 2022 post-harvest loss study:
- **16%** baseline crop loss without monitoring
- **4%** loss with active cold chain monitoring
- **12%** net loss prevented per period

Metrics calculated: loss prevented (MT + ₹), system ROI, payback period, uptime %, excursion count.  
CSV export available for reporting.

---

## Connecting Real Sensors

The simulator generates realistic sensor data across 48 facilities. To connect real hardware:

1. Add a `POST /api/readings/ingest` endpoint to `backend/app/api/readings.py`
2. ESP32 firmware POSTs JSON:

```json
{
  "sensor_code": "NASH-001",
  "temperature": 4.2,
  "humidity": 87.5,
  "ethylene_ppm": 0.12,
  "battery_pct": 92,
  "rssi": -67
}
```

> **Note:** This endpoint is not yet implemented — currently all data comes from the simulator.

---

## Environment Variables

See [`.env.example`](.env.example) for the full list with setup instructions.

| Variable                 | Default         | Description                              |
|--------------------------|-----------------|------------------------------------------|
| `DATABASE_URL`           | `postgresql://coldguard:...@db:5432/coldguard` | PostgreSQL connection        |
| `SECRET_KEY`             | `dev_secret_key...` | JWT signing key — **change in production** |
| `ANTHROPIC_API_KEY`      | _(empty)_       | Enables Hindi/Marathi alert translation  |
| `WHATSAPP_ENABLED`       | `false`         | Enable WhatsApp notifications            |
| `WHATSAPP_TOKEN`         | _(empty)_       | Meta WhatsApp Business API token         |
| `WHATSAPP_PHONE_ID`      | _(empty)_       | WhatsApp phone number ID                 |
| `SMS_ENABLED`            | `false`         | Enable SMS via fast2sms                  |
| `SMS_API_KEY`            | _(empty)_       | fast2sms API key                         |
| `NOTIFY_CRITICAL_ONLY`   | `false`         | Only send critical alerts (not warnings) |
| `ALERT_COOLDOWN_MINUTES` | `30`            | Min minutes between alerts per facility  |
| `GOOGLE_CLIENT_ID`       | _(empty)_       | Google OAuth client ID (admin login)     |
| `GOOGLE_CLIENT_SECRET`   | _(empty)_       | Google OAuth client secret               |
| `RUN_SIMULATOR`          | `true`          | Enable sensor data simulation            |

---

## Deployment

Currently deployed on **Render** (free tier):

| Service          | Render Name      | Type           |
|------------------|------------------|----------------|
| Database         | `coldguard-db`   | PostgreSQL     |
| Backend API      | `coldguard-api`  | Docker web     |
| Frontend         | `coldguard-ui`   | Static site    |

Infrastructure is defined in [`render.yaml`](render.yaml) — push to GitHub and Render auto-deploys.

### Docker Compose (local / self-hosted)

```bash
docker compose up --build
```

4 services: TimescaleDB, FastAPI backend, sensor simulator, Vite frontend.

---

## Development (without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
DATABASE_URL=postgresql://... uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## Extending the Platform

- **Add a crop type**: Add entry to `CROP_PROFILES` in `risk_engine.py`
- **Add a new alert type**: Call `create_alert()` in `alert_service.py`
- **Add a new chart**: Drop a Recharts component in `src/components/sensors/`
- **Customize advisory logic**: Edit decision matrix in `advisory_engine.py`
- **Add a notification channel**: Extend `notification_service.py`
- **Add a new mandi market**: Add to `MANDIS` list in `mandi_service.py`
