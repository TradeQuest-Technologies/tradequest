# System Architecture

## Goals
- Ship a reliable, privacy-conscious MVP on a single VPS while enabling horizontal scaling later.
- Keep services small and composable: **Broker Hub**, **Market Data**, **Journal/Analytics**, **Backtester**, **AI Orchestrator**, **Web App**.

## Services
- **Web App (Next.js)** — dashboard, journal, chat, charts, backtest UI.
- **API Gateway (FastAPI)** — public entry; routes traffic to feature services.
- **Broker Hub (FastAPI)** — connectors for Kraken & Coinbase Advanced (read-only). Normalizes fills.
- **Market Data (FastAPI)** — OHLCV/trades fetch and **candles-around-trade** helper.
- **Journal & Analytics (FastAPI)** — ingest CSV, persist trades, compute KPIs.
- **Backtester (FastAPI + workers)** — indicator engines, MC simulation, scan jobs.
- **AI Orchestrator (FastAPI)** — exposes tool endpoints used by the chatbot (tool-calling).

## Data & Infra
- **Postgres 15** — primary database for users, trades, journal, backtests, settings.
- **Redis 7** — job queues, rate limits, short-lived caches (OHLCV hot windows).
- **Object Storage (S3-compatible or local)** — screenshots, PDF reports.
- **Nginx + TLS** — reverse proxy; HTTP/2; gzip/brotli.
- **Systemd** for services; **pgbouncer** for DB pooling (later).

## Observability
- JSON structured logs; request IDs via `X-Request-ID`.
- Error tracking (Sentry or file-based fallback).
- Metrics: request latency/rate, queue depth, job runtime, connector error rate.

## Performance budgets
- App route P50 < **1.5s**; charts render < **600ms** from cached OHLCV; AI tool orchestrations < **3s** (excluding backtest compute).

## Scaling path
- Split services behind Nginx; add more workers for backtests.
- Swap local object storage to S3; add read replicas for Postgres when needed.
