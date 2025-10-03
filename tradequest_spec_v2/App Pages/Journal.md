# Journal

## Trades List
- Columns: Date/Time, Symbol, Venue, Side, Qty, Price, Fees, (PnL), R, Tags, Notes
- Filters: date range, symbol, venue, side, result, tags, R range
- Bulk: tag, export, delete
- API: GET /journal/trades?filters&limit&page

## Trade Detail
- Summary; **mini chart** (candles around trade) with trade marker
- AI analysis card (coach_trade)
- Notes & tags; rule adherence; attachments
- APIs: POST /market/context; POST /ai/tools/coach_trade; POST /journal/entry

## Sessions
- Per-day aggregates, notes, adherence
- API: GET /journal/sessions?range

## Imports
- CSV drag/drop + mapping helper; history and errors
- API: POST /journal/ingest_csv

## Tags Manager & Exports
- CRUD / merge; CSV/JSON/PDF export

## Acceptance
- Virtualized 10k rows; chart loads <600ms from cache; dedupe logic verified.
