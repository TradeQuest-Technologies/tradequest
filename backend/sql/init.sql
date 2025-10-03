-- TradeQuest Database Schema
-- Users & Billing
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE subscriptions (
  user_id UUID REFERENCES users(id),
  stripe_customer TEXT,
  plan TEXT CHECK (plan IN ('free','plus','pro')) NOT NULL DEFAULT 'free',
  status TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (user_id)
);

-- Broker Keys (encrypt key/secret via KMS or libsodium)
CREATE TABLE api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  venue TEXT,                       -- 'kraken','coinbase'
  key_enc BYTEA NOT NULL,
  secret_enc BYTEA NOT NULL,
  meta JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trades (normalized)
CREATE TABLE trades (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  account TEXT,
  venue TEXT,                       -- 'KRAKEN','COINBASE'
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

-- Journal
CREATE TABLE journal_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  trade_id UUID REFERENCES trades(id),
  ts TIMESTAMPTZ DEFAULT NOW(),
  note TEXT,
  tags TEXT[],
  attachments JSONB  -- [{"name":"cap.png","url":"..."}]
);

-- Strategies & Backtests
CREATE TABLE strategies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  name TEXT,
  spec JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE backtests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  strategy_id UUID REFERENCES strategies(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  metrics JSONB,
  equity_curve JSONB,
  trades JSONB,
  mc_summary JSONB
);

-- Metrics Cache
CREATE TABLE daily_metrics (
  user_id UUID REFERENCES users(id),
  day DATE,
  kpis JSONB,
  PRIMARY KEY (user_id, day)
);

-- Indexes for performance
CREATE INDEX idx_trades_user_id ON trades(user_id);
CREATE INDEX idx_trades_filled_at ON trades(filled_at);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_journal_entries_user_id ON journal_entries(user_id);
CREATE INDEX idx_journal_entries_trade_id ON journal_entries(trade_id);
CREATE INDEX idx_backtests_user_id ON backtests(user_id);
CREATE INDEX idx_daily_metrics_user_id ON daily_metrics(user_id);
