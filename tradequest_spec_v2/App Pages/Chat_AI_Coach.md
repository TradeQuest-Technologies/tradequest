# Chat (AI Coach)

## Purpose
Natural-language coaching and analysis with **tool-calling** for context, not generic advice.

## Tools
- GET /ai/tools/get_ohlcv?symbol&tf&limit
- GET /ai/tools/get_trades?user_id&since_minutes
- POST /ai/tools/get_trade_context {trade, tf, pre_mins, post_mins}
- POST /ai/tools/backtest_quick {spec, symbol, tf, lookback_bars}
- POST /ai/tools/coach_trade {trade_id}
- POST /ai/tools/coach_session {date}

## Behavioral Rules
- Always fetch trade context before coaching a specific trade.
- Output: 3–6 sentence diagnosis + **one** action item.

## Components
- Threads list, message stream, tool result renderer (charts/tables), prompt templates.

## Acceptance
- Tool calls logged with trace IDs; retries on transient errors; rate limits per plan.
