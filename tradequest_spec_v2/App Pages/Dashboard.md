# Dashboard

## Purpose
Give an at-a-glance view of progress, discipline, and the next best actions.

## Widgets
- Today tile: trades, (PnL*), rule adherence
- Consistency Score (weekly)
- Action Items (from /ai/tools/coach_session)
- Recent Alerts
- Performance KPIs: win rate, avg R, max DD, equity (if PnL available)
- Heatmaps: by symbol, hour, DOW

## APIs
- GET /journal/summary?range=today|7d
- GET /alerts/state/today
- POST /ai/tools/coach_session {date}
- GET /journal/kpis?range=30d
- GET /journal/heatmap?dim=symbol|hour|dow

## Edge States
- No data -> prompt connect/upload
- PnL hidden until cost basis/broker connected

## Acceptance
- Loads from cached summaries <1.5s; accessibility OK; tooltips work.
