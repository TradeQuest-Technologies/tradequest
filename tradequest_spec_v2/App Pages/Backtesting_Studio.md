# Backtesting Studio

## Strategies (v1)
- SMA Cross (fast, slow)
- RSI Revert (length, long_th, short_th)
- ATR Trail (atr_len, multiple)

## Inputs
- Data source: upload OHLCV CSV or select symbol/TF (live fetch)
- Fees/slippage (bps), horizon (bars or dates)

## Outputs
- Metrics: total return, Sharpe (simple), max DD, hit rate, trade count
- Equity curve & drawdown; per-trade list
- Monte Carlo bands (p05/median/p95)

## APIs
- POST /backtest/run (uploaded data)
- POST /backtest/quick (live-fetched)
- POST /backtest/scan (grid) — queued job (phase 1.5)

## Acceptance
- Param validation; queue heavy runs; cancel/retry; deterministic seed on MC if requested.
