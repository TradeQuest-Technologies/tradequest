# Error Catalog (Standardized)

| Code | error                | HTTP | Meaning / Fix |
|-----:|----------------------|-----:|----------------|
| 1001 | validation_error     | 422  | Missing/invalid field; message lists fields |
| 1002 | auth_required        | 401  | Session missing/expired |
| 1003 | permission_denied    | 403  | Plan gate or forbidden action |
| 1004 | rate_limited         | 429  | Too many requests; retry-after header set |
| 2001 | broker_connect_fail  | 400  | Invalid API key/secret or wrong scopes |
| 2002 | broker_scope_invalid | 400  | Withdrawal scope detected (blocked) |
| 2003 | broker_sync_error    | 502  | Upstream error from exchange; retried |
| 3001 | backtest_invalid     | 400  | Bad params; empty dataset |
| 3002 | backtest_timeout     | 504  | Computation exceeded limits |
| 4001 | ai_tool_error        | 500  | Tool threw; request_id logged |
| 5000 | internal_error       | 500  | Unhandled; alert raised |
