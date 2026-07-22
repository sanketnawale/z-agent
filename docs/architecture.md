# Architecture

> z-agent does not replace Zowe. It builds on Zowe/zOSMF.

This page summarizes z-agent's runtime components, data flows, and future
direction for Open Mainframe/Zowe reviewers.

## Overview

```
User / DevOps Pipeline
        |
        v
Django UI / REST API
        |
        v
Safety + Audit + Workflow Layer
        |
        +----> Ollama / Local AI
        |
        v
Zowe CLI / zOSMF
        |
        v
IBM Z / z/OS
```

z-agent is a layered system: the user or pipeline talks to Django, Django enforces
safety/audit and proxies to FastAPI, FastAPI calls Zowe CLI for z/OS access and
the AI gateway for explanations, and local Ollama (default) produces the AI
analysis over masked spool text.

## Runtime components

| Component | Role | Default port |
| --- | --- | --- |
| Browser/CI client | User or DevOps pipeline | n/a |
| Django frontend + REST API | UI, session, safety/audit, proxy | 8001 |
| FastAPI backend | Zowe orchestration, diagnosis, AI gateway | 3001 |
| Zowe CLI | z/OS access via z/OSMF | n/a |
| Ollama | Local AI explanation runtime | 11434 |
| SQLite (Django) | Audit log storage only | file |

## Data flow — UI spool explanation

```
Browser
  -> Django view (require_zowe_session)
  -> audit log (AI_EXPLAIN_SPOOL, metadata only)
  -> FastAPI /api/agent/explain-spool
     -> mask_spool_text (agent/masking.py)
     -> build_spool_explanation_prompt (agent/prompts.py)
     -> Ollama (agent/ollama_service.py)
  -> structured result (likely cause, evidence, next step, confidence)
  -> Django attaches audit_id
  -> UI renders structured explanation
```

## Data flow — DevOps pipeline job summary

```
CI/CD pipeline
  -> Django /api/devops/job-summary (headers, no session)
  -> audit log (DEVOPS_JOB_SUMMARY)
  -> FastAPI /api/devops/job-summary
     -> Zowe CLI fetch spool
     -> diagnose_spool (rule-based)
     -> optional: mask + Ollama explanation
     -> build_job_summary (safe_to_continue)
  -> Django attaches audit_id
  -> structured JSON to pipeline
```

## AI explanation flow

1. Python reads the spool and extracts factual diagnosis (return code, ABEND,
   message codes, evidence lines).
2. Sensitive values are masked (`agent/masking.py`) before any AI call.
3. A constrained prompt (`agent/prompts.py`) instructs the model to return a
   strict JSON object, avoid destructive actions, not invent facts, and not
   request secrets.
4. A local Ollama model produces the explanation (`agent/ollama_service.py`),
   with safe fallbacks on any failure.
5. The result is parsed into structured fields with confidence normalization.

AI is an **advisory** layer over facts Python already determined. It never
decides job results and never executes actions on IBM Z.

## DevOps pipeline flow

- Pipelines pass IBM Z / AI credentials as HTTP headers (no web session).
- `POST /api/devops/job-summary` returns `safe_to_continue` for gating.
- `POST /api/devops/incident-summary` returns a paste-ready summary with a
  recommended owner from ownership rules.
- `POST /api/devops/notify` sends (or dry-runs) a webhook; dry-run is the
  default so no network request is sent accidentally.

## Safety/audit flow

- Every significant action is checked against the current safety mode
  (`jobs/safety.py`).
- Read/analyze actions (VIEW_*, AI_EXPLAIN_*, DEVOPS_*_SUMMARY,
  DEVOPS_NOTIFY_DRY_RUN) are allowed in all modes including READ_ONLY.
- Risky actions (SUBMIT_JCL, DEVOPS_NOTIFY_SENT, ...) are gated: blocked in
  READ_ONLY, approval-gated in APPROVAL_REQUIRED, allowed in EXECUTE.
- Each action creates an audit log row with metadata only.

## What data is not stored

- Raw spool output is **never** stored in audit logs.
- Raw secrets are masked before AI analysis and never reach the model.
- Webhook notify payloads never include secrets (token/password/api_key are
  stripped).
- `.env`, `zowe.config.json`, `db.sqlite3`, certificates, and keys are
  gitignored and never committed.

## Future Kubernetes/Helm/OpenTelemetry direction

- **Kubernetes / Helm**: a container-native deployment option beyond Docker
  Compose is on the roadmap (ROADMAP.md). The Django + FastAPI split is already
  container-friendly.
- **OpenTelemetry-friendly observability**: structured logs and traces around
  the safety/audit and AI layers so operations tooling can observe z-agent
  itself.
- **SMF analytics**: behind authorized access and an explicit safety model, the
  same mask-then-analyze pattern will be applied to SMF telemetry.
- **ZoweX / MCP**: explore consuming Zowe MCP tools as an optional access
  option while keeping z-agent's safety and audit layer in control.