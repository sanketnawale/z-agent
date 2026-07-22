# Demo: AI Spool Explanation (v0.3.0)

> AI explanations are advisory only. z-agent does not replace mainframe experts,
> production change controls, or existing security processes.

This guide demonstrates the AI-assisted spool explanation workflow.

## Prerequisites

- z-agent running (Docker Compose or local dev)
- A local Ollama runtime with a pulled model, e.g.:

```bash
ollama pull llama3.2:3b
```

- An IBM Z / zOSMF connection (or a connection you can reach on the setup page)

## Safe demo flow

Use only fake job IDs, fake dataset names, and sample spool text. Never use
real production spool output or real credentials.

1. Open the app at `http://localhost:8001`.
2. Complete the setup page with a connection and select `server_ollama` /
   `llama3.2:3b`.
3. Open the **Jobs** dashboard.
4. Select a job to open its spool output.
5. In the spool viewer, click **Explain with AI** (the new v0.3.0 button).
6. The **AI Explanation** tab shows:
   - Status (explained / error)
   - Likely cause
   - Evidence from the spool
   - Suggested next step
   - Confidence (low / medium / high)
   - Model used
   - Masked flag
   - Audit ID (e.g. `AUD-000001`)
7. Open the **Audit Logs** page and confirm an `AI_EXPLAIN_SPOOL` entry exists
   with the matching audit ID.

## API usage

You can call the API directly against the FastAPI backend:

```bash
curl -X POST http://127.0.0.1:3001/api/agent/explain-spool \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "JOB12345",
    "spool_text": "IEFC621D ALLOCATION FAILED FOR USER01.PAYROLL.PROD.INPUT password=secret123"
  }'
```

Expected structured response:

```json
{
  "job_id": "JOB12345",
  "status": "explained",
  "likely_cause": "Input dataset allocation failure",
  "evidence": "Spool contains a dataset allocation or not found message.",
  "suggested_next_step": "Verify the DD statement and confirm that the dataset exists.",
  "confidence": "medium",
  "ai_used": true,
  "model": "llama3.2:3b",
  "masked": true
}
```

Note: when called directly against FastAPI, the `audit_id` field is absent
because audit logging is performed by the Django proxy for authenticated web
sessions. When called through the Django UI (`POST /explain-spool/`), the
response includes `audit_id`.

If Ollama is down:

```json
{
  "status": "error",
  "message": "AI explanation is currently unavailable.",
  "ai_used": false
}
```

## What the demo proves

The complete Sandbox-readiness workflow:

```
IBM Z job spool output
  -> sensitive data masking
  -> Ollama AI explanation
  -> structured result
  -> audit log entry
  -> UI/API result
```

## What it does NOT prove

- The AI explanation is not guaranteed to be correct.
- Masking reduces but does not fully eliminate information leakage on unusual
  formats.
- Direct FastAPI API calls are not audited (audit logging is session-based in
  the Django layer).