# Event Tracking (Analytics)

## Identity
- user_id, plan, tz, signup_date

## Events
- app_open {path}
- broker_connected {venue}
- import_csv {rows, venue_guess}
- trade_view {trade_id}
- coach_trade_run {trade_id, duration_ms, tools_used}
- backtest_run {strategy, symbol, tf, lookback, duration_ms}
- rules_set {daily_stop, max_trades, cooldown}
- alert_triggered {type, value}
- weekly_pdf_generated {pages, duration_ms}

All events include request_id, ts, client version.
