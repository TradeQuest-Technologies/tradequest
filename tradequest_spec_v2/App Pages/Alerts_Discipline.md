# Alerts & Discipline

## Rules
- Daily stop (amount/%), max trades, cooldown, quiet hours
- API: /alerts/rules (CRUD)

## Channels
- Telegram link/unlink; Email verify/test
- API: /alerts/channels

## History & Streaks
- Timeline of stop hits, cooldowns, violations; badges for streaks
- APIs: /alerts/history, /alerts/streaks

## Acceptance
- Reliable delivery; idempotent rule triggers; timezone-aware quiet hours.
