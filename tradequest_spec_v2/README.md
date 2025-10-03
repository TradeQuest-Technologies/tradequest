# TradeQuest — Full Product & UX Spec
**Version:** MVP v1.0 • **Last updated:** 2025-09-25 19:26 UTC

This repository contains a **page-by-page, dev-ready specification** for the TradeQuest platform (journal + AI analysis + AI backtesting + broker integrations + chat tools).  
Each document includes: **Purpose, Primary Actions, Components, Data & API, Validation/Rules, States, Analytics, Acceptance Criteria, Security/Perf Budgets, Open Questions**.

## How to use this folder
- Start with **`/Architecture/`** for the high-level architecture, data model, API routes, and security model.
- For feature work, open the page under **`/App Pages/`** (e.g., `Journal`, `Backtesting`).
- For marketing/site work, see **`/Public Site/`**.
- Phase-2+ scopes live under **`/Future/`**.
- Stripe/business descriptors are in **`/Biz/`**.

## Table of Contents
- **Architecture/**
  - `System_Architecture.md` — services, deployment, observability
  - `Data_Model_DDL.sql` — SQL DDL for all core tables
  - `API_Routes_Outline.yaml` — route map with request/response shapes
  - `Detailed_API_Spec.yaml` — full OpenAPI with schemas & examples
  - `Error_Catalog.md` — unified error codes
  - `Rate_Limits.md` — per-plan & per-route
  - `Event_Telemetry.md` — analytics events
  - `Logging_Observability.md` — logs, metrics, alerts
  - `Security_Model.md` — auth, key vault, scopes, rate limits
  - `Data_Lifecycle.md` — collection, storage, retention, deletion
  - `Threat_Model.md` — risks & mitigations
  - `Ops_Deployment_Guide.md`, `Ops_Nginx_Config.txt`, `Ops_Systemd_Units.md`, `Ops_Env_Vars.md`, `Ops_Backup_Restore.md`
- **Public Site/**
  - `Landing.md`, `Features.md`, `Pricing.md`, `Docs_Public.md`, `Legal.md`, `Auth.md`
- **App Pages/**
  - `Onboarding_Wizard.md`
  - `App_Shell.md`
  - `Dashboard.md`
  - `Chat_AI_Coach.md`
  - `Chat_AI_Prompts_and_Tools.md`
  - `Journal.md`
  - `Journal_Trade_Detail_Spec.md`
  - `Backtesting_Studio.md`
  - `Backtesting_Strategies_Spec.md`
  - `Market_Explorer.md`
  - `Market_Explorer_Charts.md`
  - `Reports.md`
  - `Alerts_Discipline.md`
  - `Integrations.md`
  - `Integrations_Kraken_Mapping.md`
  - `Integrations_Coinbase_Advanced_Mapping.md`
  - `Settings.md`
  - `Help_Docs.md`
- **Future/**
  - `Team_Coach_Workspace.md`
  - `Admin_Internal.md`
- **Biz/**
  - `Stripe_Business_Description.txt`
  - `Pricing_Plan_Gates.md`

**Note:** All broker connections are **read-only**, educational product, no investment advice.
