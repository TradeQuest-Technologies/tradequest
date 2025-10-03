-- Users & Billing
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  tz TEXT DEFAULT 'America/New_York',
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS subscriptions (
  user_id UUID REFERENCES users(id),
  stripe_customer TEXT,
  plan TEXT CHECK (plan IN ('free','plus','pro')) NOT NULL DEFAULT 'free',
  status TEXT,
  updated_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (user_id)
);

-- API Keys (encrypted fields stored as bytea or text w/ KMS)
CREATE TABLE IF NOT EXISTS api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  venue TEXT,                         -- 'kraken','coinbase'
  key_enc BYTEA NOT NULL,
  secret_enc BYTEA NOT NULL,
  meta JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Trades (normalized)
CREATE TABLE IF NOT EXISTS trades (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  account TEXT,
  venue TEXT,                         -- 'KRAKEN','COINBASE'
  symbol TEXT,
  side TEXT CHECK (side IN ('buy','sell')),
  qty NUMERIC,
  avg_price NUMERIC,
  fees NUMERIC DEFAULT 0,
  pnl NUMERIC DEFAULT 0,
  submitted_at TIMESTAMPTZ,
  filled_at TIMESTAMPTZ NOT NULL,
  order_ref TEXT,
  session_id UUID,
  raw JSONB
);

-- Journal entries
CREATE TABLE IF NOT EXISTS journal_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  trade_id UUID REFERENCES trades(id),
  ts TIMESTAMPTZ DEFAULT now(),
  note TEXT,
  tags TEXT[],
  attachments JSONB
);

-- Strategies & Backtests
CREATE TABLE IF NOT EXISTS strategies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  name TEXT,
  spec JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS backtests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  strategy_id UUID REFERENCES strategies(id),
  created_at TIMESTAMPTZ DEFAULT now(),
  metrics JSONB,
  equity_curve JSONB,
  trades JSONB,
  mc_summary JSONB
);

-- Daily metrics cache
CREATE TABLE IF NOT EXISTS daily_metrics (
  user_id UUID REFERENCES users(id),
  day DATE,
  kpis JSONB,
  PRIMARY KEY (user_id, day)
);
