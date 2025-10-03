# Logging & Observability

## Log format
JSON lines with fields: ts, level, service, request_id, user_id?, route, latency_ms, status, message, meta

## Metrics
- http_requests_total{route,status}
- http_request_duration_seconds{route,quantile}
- jobs_in_queue{type}
- job_duration_seconds{type}
- broker_sync_failures_total{venue}
- backtest_runs_total{plan}
- ai_tool_calls_total{tool}

## Alerts
- 5xx rate > 1% for 5 minutes
- broker_sync_error > threshold
- backtest timeouts spike
