# Security Model

## Guiding principles
- **Least privilege**: Read-only exchange keys; never request withdrawal scopes.
- **Defense-in-depth**: TLS, httpOnly cookies, CSRF for mutating routes, rate limits, audit logs.
- **Privacy**: Data export & delete endpoints; minimize PII (email only).

## Auth
- Magic-link email sign-in; sessions stored in httpOnly secure cookies; short JWT TTL + refresh.

## Key Vault
- Exchange keys stored AES-GCM encrypted at rest; per-record random IV; KMS-managed master key or libsodium sealed boxes.
- Access limited to Broker Hub service; never logged.

## Rate limits
- Per-IP and per-user gates via Redis (e.g., 60 req/min for public routes; plan-based for heavy routes/backtests).

## Data retention
- Journal/Trades: until user deletes. Access logs retained 30–90 days.
- Backtests: user-owned; can purge on demand.

## Compliance posture (MVP)
- Educational product; no investment advice. COPPA/teen notice (16+). GDPR-style data rights honored (export/delete).
