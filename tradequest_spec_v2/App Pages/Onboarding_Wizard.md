# Onboarding Wizard

## Steps
1) Welcome (16+ consent)
2) Choose Plan (Free/Plus/Pro) -> Stripe checkout for paid
3) Connect a broker (Kraken, Coinbase Advanced) — optional skip
4) Import recent trades (auto if connected; otherwise CSV upload)
5) Set discipline rules (daily stop, max trades, cooldown)
6) Pick goals (risk %, target dd%, learning focus)
7) Tour / Finish

## APIs & Data
- POST /billing/checkout
- POST /broker/connect/{venue}
- GET /broker/fills (last 7d) -> insert into trades
- POST /journal/ingest_csv
- POST /alerts/rules
- POST /profile/goals

## Validation
- Keys must be read-only scopes; test call during connect
- CSV mapping preview (5 rows); duplicate trade detection
