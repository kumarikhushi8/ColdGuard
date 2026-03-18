-- Enable TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Cold storage facilities
CREATE TABLE IF NOT EXISTS facilities (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    location    TEXT NOT NULL,
    owner_name  TEXT NOT NULL,
    owner_phone TEXT NOT NULL,
    capacity_mt NUMERIC(10,2),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Sensor nodes per facility
CREATE TABLE IF NOT EXISTS sensors (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    facility_id UUID REFERENCES facilities(id) ON DELETE CASCADE,
    sensor_code TEXT UNIQUE NOT NULL,
    type        TEXT NOT NULL CHECK (type IN ('temperature','humidity','ethylene','combined')),
    location    TEXT,
    active      BOOLEAN DEFAULT TRUE,
    installed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Time-series sensor readings (hypertable)
CREATE TABLE IF NOT EXISTS sensor_readings (
    time        TIMESTAMPTZ NOT NULL,
    sensor_id   UUID NOT NULL REFERENCES sensors(id),
    temperature NUMERIC(5,2),
    humidity    NUMERIC(5,2),
    ethylene_ppm NUMERIC(8,4),
    battery_pct NUMERIC(5,2),
    rssi        INTEGER
);
SELECT create_hypertable('sensor_readings', 'time', if_not_exists => TRUE);
CREATE INDEX ON sensor_readings (sensor_id, time DESC);

-- Spoilage risk scores (computed by ML model)
CREATE TABLE IF NOT EXISTS risk_scores (
    time          TIMESTAMPTZ NOT NULL,
    facility_id   UUID NOT NULL REFERENCES facilities(id),
    risk_score    NUMERIC(5,4) NOT NULL,  -- 0.0 to 1.0
    risk_level    TEXT NOT NULL CHECK (risk_level IN ('low','medium','high','critical')),
    crop_type     TEXT,
    contributing_factors JSONB
);
SELECT create_hypertable('risk_scores', 'time', if_not_exists => TRUE);

-- Alerts
CREATE TABLE IF NOT EXISTS alerts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    facility_id UUID REFERENCES facilities(id),
    sensor_id   UUID REFERENCES sensors(id),
    alert_type  TEXT NOT NULL,
    severity    TEXT NOT NULL CHECK (severity IN ('info','warning','critical')),
    message     TEXT NOT NULL,
    message_hi  TEXT,
    message_mr  TEXT,
    acknowledged BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    ack_at      TIMESTAMPTZ
);

-- Mandi price snapshots
CREATE TABLE IF NOT EXISTS mandi_prices (
    time        TIMESTAMPTZ NOT NULL,
    crop        TEXT NOT NULL,
    market      TEXT NOT NULL,
    price_min   NUMERIC(10,2),
    price_max   NUMERIC(10,2),
    price_modal NUMERIC(10,2),
    unit        TEXT DEFAULT 'quintal'
);
SELECT create_hypertable('mandi_prices', 'time', if_not_exists => TRUE);

-- Seed demo data
INSERT INTO facilities (id, name, location, owner_name, owner_phone, capacity_mt) VALUES
    ('a1b2c3d4-0000-0000-0000-000000000001', 'Nashik Cold Hub 1', 'Nashik, Maharashtra', 'Rajesh Patil', '+919876543210', 500),
    ('a1b2c3d4-0000-0000-0000-000000000002', 'Pune Agri Store', 'Pune, Maharashtra', 'Sunita Deshpande', '+919876543211', 300),
    ('a1b2c3d4-0000-0000-0000-000000000003', 'Solapur Fruits Hub', 'Solapur, Maharashtra', 'Mahesh Jadhav', '+919876543212', 750)
ON CONFLICT DO NOTHING;

INSERT INTO sensors (id, facility_id, sensor_code, type, location) VALUES
    ('b1b2c3d4-0000-0000-0000-000000000001', 'a1b2c3d4-0000-0000-0000-000000000001', 'NASH-001', 'combined', 'Zone A - Main chamber'),
    ('b1b2c3d4-0000-0000-0000-000000000002', 'a1b2c3d4-0000-0000-0000-000000000001', 'NASH-002', 'combined', 'Zone B - Entry'),
    ('b1b2c3d4-0000-0000-0000-000000000003', 'a1b2c3d4-0000-0000-0000-000000000002', 'PUNE-001', 'combined', 'Main chamber'),
    ('b1b2c3d4-0000-0000-0000-000000000004', 'a1b2c3d4-0000-0000-0000-000000000003', 'SOLP-001', 'combined', 'Primary zone'),
    ('b1b2c3d4-0000-0000-0000-000000000005', 'a1b2c3d4-0000-0000-0000-000000000003', 'SOLP-002', 'combined', 'Secondary zone')
ON CONFLICT DO NOTHING;

-- ─── Auth tables ──────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email         TEXT UNIQUE,
    phone         TEXT UNIQUE,
    name          TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('admin','operator','farmer')),
    password_hash TEXT,                    -- null for OTP-only users
    google_sub    TEXT UNIQUE,             -- Google OAuth subject ID
    active        BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    last_login    TIMESTAMPTZ
);

-- OTP store for phone login (auto-expire after 10 min)
CREATE TABLE IF NOT EXISTS phone_otps (
    phone      TEXT PRIMARY KEY,
    otp_hash   TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    attempts   INTEGER DEFAULT 0
);

-- Refresh tokens (for stateless JWT rotation)
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Operator → facility mapping (who manages what)
CREATE TABLE IF NOT EXISTS operator_facilities (
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    facility_id UUID REFERENCES facilities(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, facility_id)
);

-- Farmer → facility mapping (who stores where)
CREATE TABLE IF NOT EXISTS farmer_facilities (
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    facility_id UUID REFERENCES facilities(id) ON DELETE CASCADE,
    crop        TEXT,
    PRIMARY KEY (user_id, facility_id)
);

-- Seed admin user (password: Admin@123)
INSERT INTO users (email, name, role, password_hash) VALUES
    ('admin@coldguard.in', 'ColdGuard Admin', 'admin',
     '$2b$12$uiOt2lvJOLxw5yEaXx4pkOlnKaDT.zjsWUZ7w./MkUhrg36pvUPEW')
ON CONFLICT DO NOTHING;
