-- Initialize TradeQuest database
-- This script runs when the PostgreSQL container starts for the first time

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone
SET timezone = 'UTC';

-- Create database if it doesn't exist (this is handled by POSTGRES_DB env var)
-- But we can add any additional setup here

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE tradequest TO tradequest;

-- Create schema if needed
-- CREATE SCHEMA IF NOT EXISTS tradequest;

-- Note: Tables will be created by SQLAlchemy models
