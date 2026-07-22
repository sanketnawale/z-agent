# AI Operations

> AI explanations are advisory only. z-agent does not replace mainframe experts,
> production change controls, or existing security processes.

## Overview

The v0.3.0 AI Operations Preview adds an AI-assisted spool explanation workflow:

```
IBM Z job spool output
  -> sensitive data masking
  -> safe prompt
  -> local Ollama model
  -> structured result
  -> audit log entry
  -> UI / API result
```

Z-agent does **not** send raw secrets or private dataset names to the AI model.
Spool text is masked first, then analyzed.

## How AI explanation works

1. A user opens a job spool and clicks **Explain with AI**.
2. The Django frontend sends `{ job_id, spool_text }` to its proxy endpoint
   `POST /explain-spool/`.
3. Django writes an `AI_EXPLAIN_SPOOL` audit log entry and forwards the request
   to the FastAPI backend endpoint `POST /api/agent/explain-spool`.
4. The FastAPI backend masks the spool text (`agent/masking.py`), builds a
   safe prompt (`agent/prompts.py`), and calls Ollama
   (`agent/ollama_service.py`).
5. The structured result is returned and, on the UI side, an `audit_id` is
   attached so the explanation is traceable.

## Structured response (success)

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
  "masked": true,
  "audit_id": "AUD-000001"
}
```

## Safe error response

When Ollama is unavailable or fails, z-agent never exposes raw exceptions:

```json
{
  "status": "error",
  "message": "AI explanation is currently unavailable.",
  "ai_used": false
}
```

The `audit_id` is attached by the Django layer for UI requests. Direct calls to
the FastAPI `POST /api/agent/explain-spool` endpoint will not include an
`audit_id` because the audit log is tied to the authenticated web session.

## What data is masked

Before any spool text reaches the model, `agent/masking.py` redacts:

- email addresses
- IPv4 addresses
- `password`, `token`, `api_key`, `secret`, and similar assignments
- URLs and `host=` assignments
- mainframe dataset names matching common uppercase patterns, e.g.
  `USER01.PAYROLL.PROD.INPUT` becomes `<DATASET_NAME>`
- long numeric / account-like identifiers

Message codes (such as `IEFC621D`, `IGYPS2113-E`) and single uppercase tokens
are intentionally left visible so the model can reason about the failure.

## What audit log entry is created

Each AI explanation request creates an `AI_EXPLAIN_SPOOL` audit log entry with:

- timestamp (`created_at`)
- action type (`AI_EXPLAIN_SPOOL`)
- job ID (`target`)
- safety mode
- status (`ALLOWED` on success, `FAILED` when the AI service errors)
- username (from the web session)

Extra metadata (`ai_used`, `model`, `masked`) is stored in the `details` field.
**Raw spool output is never stored in the audit log.**

## Safety mode behavior

`AI_EXPLAIN_SPOOL` is a **read/analyze** action. It does not modify anything on
IBM Z, so it is allowed in `READ_ONLY` mode (and every other safety mode). It
is registered in `SAFE_READ_ACTIONS` in `jobs/safety.py`.

## How Ollama is configured

Ollama settings come from the environment or the per-user AI profile:

```bash
OLLAMA_BASE_URL=http://127.0.0.1:11434   # base URL; /api/generate is appended
OLLAMA_MODEL=llama3.2:3b                  # model tag
```

For Docker Compose, use `OLLAMA_URL=http://ollama:11434/api/generate` (the
project keeps backward compatibility with the `OLLAMA_URL` variable).

## Limitations

- AI explanations are advisory only and may be wrong.
- Masking is conservative; some values may still be recognizable in context.
- Confidence is model-derived and should not be treated as a guarantee.
- The structured parser is best-effort. If the model does not return JSON,
  z-agent falls back to a labelled-section parser and confidence is set to
  `low`.
- Direct calls to the FastAPI endpoint skip Django audit logging.