# DevOps Integration

> z-agent does not replace Zowe. It builds on Zowe/zOSMF.

This document explains how DevOps and CI/CD pipelines can use z-agent to get
structured IBM Z job summaries, incident summaries, and dry-run webhook
notifications.

```
CI/CD pipeline
  -> calls z-agent API
  -> z-agent checks IBM Z job/spool result
  -> z-agent generates structured job summary
  -> optional AI explanation
  -> optional webhook notification
  -> audit log records the action
  -> pipeline receives clear JSON result
```

> Do not use production IBM Z credentials, real spool output, private SMF
> data, or company-sensitive data in public examples or issues.

## Endpoints

z-agent exposes three pipeline-friendly endpoints. The pipeline calls the
Django server (default port 8001), which writes an audit log entry and
attaches an `audit_id`, then proxies to the FastAPI backend (port 3001) which
performs the IBM Z/AI work.

### 1. Job summary

```
POST /api/devops/job-summary
```

Request:

```json
{
  "job_id": "JOB12345",
  "job_name": "PAYROLL01",
  "include_ai_explanation": true
}
```

Response (AI available):

```json
{
  "job_id": "JOB12345",
  "job_name": "PAYROLL01",
  "status": "FAILED",
  "return_code": "RC=12",
  "result": "failure",
  "likely_cause": "Input dataset allocation failure",
  "evidence": "Spool contains a dataset allocation failure message.",
  "suggested_next_step": "Verify the DD statement and dataset name.",
  "confidence": "medium",
  "ai_used": true,
  "audit_id": "AUD-000123",
  "safe_to_continue": false
}
```

Response (AI unavailable):

```json
{
  "job_id": "JOB12345",
  "status": "FAILED",
  "return_code": "RC=12",
  "result": "failure",
  "ai_used": false,
  "message": "AI explanation unavailable. Basic job summary returned.",
  "safe_to_continue": false
}
```

The most important field for pipelines is `safe_to_continue`: `true` only when
the job clearly succeeded (`status` == `SUCCESS`).

### 2. Incident summary

```
POST /api/devops/incident-summary
```

Request:

```json
{
  "job_id": "JOB12345",
  "job_name": "PAYROLL01",
  "spool_text": "...",
  "include_ai_explanation": true
}
```

Response:

```json
{
  "title": "IBM Z job PAYROLL01 failed with RC=12",
  "severity": "medium",
  "summary": "The job failed due to a likely input dataset allocation issue.",
  "evidence": "Spool contains a dataset allocation failure message.",
  "recommended_owner": "Payroll Team",
  "suggested_next_step": "Verify the DD statement and dataset availability.",
  "audit_id": "AUD-000124"
}
```

When `spool_text` is provided, z-agent masks it and diagnoses locally without
fetching from IBM Z. When omitted, z-agent fetches the job spool via Zowe.

### 3. Webhook notify

```
POST /api/devops/notify
```

Request:

```json
{
  "webhook_url": "https://example.org/webhook",
  "job_id": "JOB12345",
  "job_name": "PAYROLL01",
  "summary": "Job failed with RC=12",
  "dry_run": true
}
```

`dry_run` defaults to `true`. In dry-run mode z-agent returns the payload that
would be sent without touching the network:

```json
{
  "status": "dry_run",
  "message": "Notification payload generated but not sent.",
  "payload": {
    "job_id": "JOB12345",
    "job_name": "PAYROLL01",
    "summary": "Job failed with RC=12",
    "source": "z-agent"
  }
}
```

## Authentication for pipelines

DevOps pipelines do not use web sessions. Pass IBM Z and AI credentials as
HTTP headers on each request:

| Header | Purpose |
| --- | --- |
| `X-Zowe-Host` | z/OSMF host |
| `X-Zowe-Port` | z/OSMF port |
| `X-Zowe-User` | IBM Z user ID |
| `X-Zowe-Password` | IBM Z password |
| `X-Zowe-RU` | rejectUnauthorized (true/false) |
| `X-AI-Provider` | AI provider (server_ollama, rule_based, ...) |
| `X-AI-Model` | AI model tag |
| `X-Ollama-URL` | Ollama base URL |
| `X-Ownership-Rules-Path` | optional override for ownership rules file |

Store these in your pipeline's secret store (Jenkins credentials, GitHub
secrets, GitLab CI variables). Never hardcode them in files.

## Safety and audit behavior

- `DEVOPS_JOB_SUMMARY` and `DEVOPS_INCIDENT_SUMMARY` are read/analyze actions,
  allowed in every safety mode including `READ_ONLY`.
- `DEVOPS_NOTIFY_DRY_RUN` is a read action (always allowed).
- `DEVOPS_NOTIFY_SENT` (real webhook send) is a **risky** action: it is only
  allowed in `EXECUTE` mode (or `APPROVAL_REQUIRED` with approval). In
  `READ_ONLY` mode a real send is blocked and the response tells the caller to
  use `dry_run=true`.
- Every DevOps request creates an audit log entry with metadata only —
  timestamp, action type, job ID, job name, AI used, dry-run flag, safety mode,
  and status. Raw spool output is never stored in audit logs.

## Audit action types

- `DEVOPS_JOB_SUMMARY`
- `DEVOPS_INCIDENT_SUMMARY`
- `DEVOPS_NOTIFY_DRY_RUN`
- `DEVOPS_NOTIFY_SENT`
- `DEVOPS_NOTIFY_FAILED`

## Limitations

- z-agent is not production-ready without a security review.
- AI explanations are advisory only.
- Masking reduces but does not fully eliminate information leakage on unusual
  formats.
- Real webhook sends are gated by the safety mode; use dry-run by default.
- Direct FastAPI endpoint calls skip the Django audit logging/`audit_id` —
  call the Django endpoints for audited responses.

See `docs/pipeline-examples.md` for Jenkins/GitHub Actions examples and
`docs/incident-routing.md` for ownership routing.