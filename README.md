# ColdGuard — Cold Chain Intelligence Platform

Real-time spoilage risk monitoring for Indian agricultural cold storage.  
Sensor data → ML risk scoring → multilingual farmer alerts.

---

## Quick Start

```bash
# 1. Clone / enter project
cd coldguard

# 2. (Optional) Set Anthropic key for Hindi/Marathi alert translation
export ANTHROPIC_API_KEY=sk-ant-...

# 3. Start everything
./start.sh
```

| Service       | URL                          |
|---------------|------------------------------|
| Dashboard     | http://localhost:5173        |
| API (Swagger) | http://localhost:8000/docs   |
| PostgreSQL     | localhost:5432               |

---

## Architecture

```
coldguard/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI entry point
│       ├── core/
│       │   ├── config.py        # Settings (env vars)
│       │   └── database.py      # asyncpg connection pool
│       ├── api/
│       │   ├── dashboard.py     # /api/dashboard/summary  ← main endpoint
│       │   ├── facilities.py    # /api/facilities/
│       │   ├── sensors.py       # /api/sensors/
│       │   ├── readings.py      # /api/readings/
│       │   └── alerts.py        # /api/alerts/
│       ├── ml/
│       │   └── risk_engine.py   # Spoilage risk model (0–1 score)
│       └── services/
│           ├── alert_service.py # Alert creation + Claude translation
│           └── simulator.py     # Fake sensor data generator
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── DashboardPage.jsx
│       │   ├── FacilityPage.jsx
│       │   └── AlertsPage.jsx
│       ├── components/
│       │   ├── dashboard/       # StatCard, FacilityCard, RiskGauge
│       │   ├── alerts/          # AlertItem
│       │   └── sensors/         # TrendChart
│       ├── hooks/usePolling.js  # Auto-refresh hook
│       └── lib/
│           ├── api.js           # API client
│           └── utils.js         # Formatters
├── infra/
│   └── init.sql                 # TimescaleDB schema + seed data
└── docker-compose.yml
```

---

## How the Risk Engine Works

File: `backend/app/ml/risk_engine.py`

Computes a 0–1 spoilage risk score using 4 weighted factors:

| Factor                    | Weight | Source |
|---------------------------|--------|--------|
| Temperature deviation      | 40%    | ICAR post-harvest research |
| Excursion duration         | 25%    | Time above safe threshold |
| Relative humidity          | 20%    | Crop-specific RH profiles |
| Ethylene concentration     | 15%    | Ripening gas ppm |

Output passes through a sigmoid function to smooth the 0–1 boundary.  
Risk levels: `low` < 0.30 < `medium` < 0.55 < `high` < 0.75 < `critical`

Crop profiles supported: tomato, onion, potato, mango, grapes, default.

---

## Alert Translation

If `ANTHROPIC_API_KEY` is set, every alert is translated into Hindi and Marathi  
via Claude API (`claude-sonnet-4-6`). Farmers receive alerts in their language.

Without the key, alerts remain in English only.

---

## Connecting Real Sensors

Replace the simulator with real ESP32 firmware that POSTs to:

```
POST /api/readings/ingest
{
  "sensor_code": "NASH-001",
  "temperature": 4.2,
  "humidity": 87.5,
  "ethylene_ppm": 0.12,
  "battery_pct": 92,
  "rssi": -67
}
```

Add this endpoint to `backend/app/api/readings.py` when ready for hardware.

---

## Environment Variables

| Variable             | Default                          | Description                  |
|----------------------|----------------------------------|------------------------------|
| `DATABASE_URL`       | postgresql://coldguard:...       | PostgreSQL connection string |
| `SECRET_KEY`         | dev_secret_key                   | Change in production         |
| `ANTHROPIC_API_KEY`  | (empty)                          | Enables alert translation    |

---

## Development (without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
DATABASE_URL=postgresql://... uvicorn app.main:app --reload

# Simulator (separate terminal)
cd backend
python -m app.services.simulator

# Frontend
cd frontend
npm install
npm run dev
```

---

## Extending the Platform

- **Add a crop type**: Edit `CROP_PROFILES` in `risk_engine.py`
- **Add a new alert type**: Call `create_alert()` in `alert_service.py`
- **Add a new chart**: Drop a Recharts component in `src/components/sensors/`
- **WhatsApp integration**: Replace SMS stub in `alert_service.py` with Twilio/Meta API
