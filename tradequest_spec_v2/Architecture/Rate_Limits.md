# Rate Limits (per user unless noted)

## REST endpoints
- Public (unauth): 60 req/min/IP
- Authenticated default: 120 req/min
- Market OHLCV: 60 req/min
- Backtests: queued; see below

## Backtests (per plan)
- Free: 1/day; max lookback 5k bars; 30s runtime cap
- Plus: 10/day; max lookback 20k bars; 60s runtime cap
- Pro: unlimited (fair use: 100/day); max lookback 50k bars; 120s cap

## AI tools
- coach_trade: Free 0/day, Plus 20/day, Pro 100/day
- get_trade_context: 120/min but cached per trade for 10 minutes
