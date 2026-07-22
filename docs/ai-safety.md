# AI Safety

> AI explanations are advisory only. z-agent does not replace mainframe experts,
> production change controls, or existing security processes.

## Principles

z-agent treats AI as an **advisory** layer over Zowe/zOSMF. It never lets the
AI execute destructive actions, and it never sends raw secrets to a model.

1. **Mask before analyze.** Spool text is scrubbed before it is sent to any AI
   model (see `agent/masking.py`).
2. **Never store raw spool in audit logs.** Audit entries store metadata only
   (job ID, model, ai_used, masked, status).
3. **Never expose raw exceptions to users.** When the AI service fails, z-agent
   returns a generic, safe error message.
4. **Do not recommend destructive actions.** The prompt explicitly forbids
   destructive recommendations and bypassing security controls.
5. **Read-only by design.** AI explanation is classified as a read/analyze
   action and is allowed in `READ_ONLY` safety mode.

## What gets masked

`agent.masking.mask_spool_text` redacts:

- email addresses -> `<EMAIL>`
- IPv4 addresses -> `<IP_ADDRESS>`
- `password` / `token` / `api_key` / `secret` / similar assignments ->
  `key=<REDACTED>`
- URLs -> `<URL>`
- `host=` assignments -> `<HOSTNAME_REDACTED>`
- mainframe dataset names (uppercase, dot-separated, at least one dot) ->
  `<DATASET_NAME>`
- long numeric / account-like identifiers -> `<ACCOUNT_ID>`

Single uppercase tokens and message codes (e.g. `IEFBR14`, `IEFC621D`,
`IGYPS2113-E`) are kept visible so the model can reason about the failure.

## Prompt constraints

The prompt (`agent/prompts.py`) instructs the model to:

- analyze the masked spool and return a strict JSON object
- cite evidence from the spool
- suggest safe next steps
- avoid destructive actions
- say when confidence is low
- not invent missing facts
- not expose or request secrets
- not recommend bypassing security controls

## Audit logging

Every AI explanation request creates an audit log entry with action
`AI_EXPLAIN_SPOOL`. Status values:

- `ALLOWED` - the AI returned a structured explanation
- `FAILED` - the AI service was unavailable or errored
- `BLOCKED` - a safety mode blocked the action (not expected for this action)

Audit details include `ai_used`, `model`, and `masked` flags, but **never** the
raw spool output or any secret value. Existing line-level secret masking in
`jobs/safety.mask_text` is also applied to audit fields as defense in depth.

## Failure handling

The Ollama service (`agent/ollama_service.py`) catches connection errors,
timeouts, HTTP errors, and unexpected exceptions. It never raises into the web
app. On any failure it returns:

```json
{ "status": "error", "message": "AI explanation is currently unavailable.", "ai_used": false }
```

## Verification

Tests cover:

- masking of passwords, dataset names, emails, IPs, URLs, account IDs
- that secrets do not reach the model prompt
- prompt builder safety instructions
- structured response parsing (success and missing fields)
- Ollama connection/timeout/HTTP failure returning safe errors
- audit log creation on success and failure
- raw secrets not persisted in audit logs