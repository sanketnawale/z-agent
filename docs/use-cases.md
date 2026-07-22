# Use Cases

> z-agent does not replace Zowe. It builds on Zowe/zOSMF to add a safe,
> auditable, AI-assisted operations layer.

These are practical, real-world use cases z-agent is designed to support today
or in the near future. AI explanations are **advisory only** and do not replace
mainframe experts or production change controls.

## Current use cases

### 1. Operations team investigates a failed job

- **Problem**: A batch job ends with a non-zero return code or ABEND. The spool
  is long and the on-call operator is not a deep mainframe expert.
- **Current workflow**: Open the spool in a tool like SDSF or Zowe, scroll
  through JESMSGLG/JESJCL/JESYSMSG, search for message codes, and manually map
  them to a root cause — or escalate to a senior mainframer.
- **z-agent workflow**: Open the job in z-agent, read the rule-based diagnosis
  (return code, ABEND, evidence lines), then click **Explain with AI**. The
  spool is masked, sent to a local Ollama model, and returned as a structured
  result: likely cause, evidence, suggested next step, confidence, and an audit
  ID.
- **Value**: Faster triage with cited evidence and an editable audit trail, so
  hand-offs to escalation are clearer and the AI analysis never sends raw secrets
  to a model.

### 2. Developer explains a JCL/spool error

- **Problem**: A developer submits JCL that fails with an `IEFC` allocation or
  syntax error and does not understand the message.
- **Current workflow**: Paste the spool into search, ask a senior, or read
  documentation for the specific message code.
- **z-agent workflow**: Open the job spool, get the rule-based diagnosis, and
  read an AI explanation that ties the message code to plain-English meaning and
  a safe next step.
- **Value**: Learns the meaning of message codes with evidence attached, faster
  self-service, and no raw secrets leaving the local model.

### 3. DevOps pipeline gets a job failure summary

- **Problem**: A CI/CD pipeline submits a mainframe job and needs a concise,
  structured failure summary for triage.
- **Current workflow**: The pipeline captures raw spool text and a human has to
  parse it, or a separate script tries to grep for return codes.
- **z-agent workflow**: Call `POST /api/agent/explain-spool` with `{ job_id,
  spool_text }`. z-agent masks sensitive values, calls Ollama, and returns a
  structured result (`likely_cause`, `evidence`, `suggested_next_step`,
  `confidence`, `ai_used`, `masked`).
- **Value**: A consistent, machine-readable failure summary that can be attached
  to an incident ticket, with sensitive data already redacted.

### 4. Support team generates an incident summary

- **Problem**: Support needs a quick, consistent first-pass summary of a failed
  job for an incident report.
- **Current workflow**: Manually copy key lines from spool, describe the ABEND,
  and write the summary by hand.
- **z-agent workflow**: Run an AI explanation, capture the structured fields plus
  the audit ID, and use them as the basis of the incident summary.
- **Value**: A repeatable summary format with already-cited evidence and a
  traceable audit entry, with secrets masked.

### 5. Junior mainframe developer onboarding

- **Problem**: New mainframe developers find raw spool output intimidating and
  hard to learn from.
- **Current workflow**: Shadow a senior, read manuals, or guess.
- **z-agent workflow**: Browse jobs and datasets in a simple web UI, read
  plain-English explanations tied to real message codes and evidence, and
  explore datasets/USS safely in `READ_ONLY` mode.
- **Value**: Faster, safer onboarding with `READ_ONLY` safety preventing
  accidental writes, and explanations that teach message-code meaning.

## Future use cases

### 6. Responsible team notification

- **Problem**: When a job fails, the right team should be notified with enough
  context to act, without noise.
- **Current workflow**: Generic alerts with raw log dumps that recipients must
  decode.
- **z-agent workflow (future)**: Use the structured explanation (likely cause,
  confidence, suggested next step) as the payload for a notification, routed to
  the responsible team.
- **Value**: Higher-signal notifications based on structured, masked analysis
  instead of raw dumps.

### 7. SMF telemetry analysis

- **Problem**: SMF records contain rich operational telemetry, but analyzing them
  requires authorized access and careful handling.
- **Current workflow**: Specialized tools or consultants; sensitive data often
  requires restricted environments.
- **z-agent workflow (future)**: Under authorized access and an explicit safety
  model, apply the same mask-then-analyze pattern to SMF telemetry, producing
  advisory summaries with audit logging.
- **Value**: Open, auditable, local-first SMF summaries that respect the
  sensitivity of the data and keep humans in the loop.

## Notes

- All AI explanations are advisory only.
- z-agent never modifies IBM Z during AI analysis; AI explanation is a
  read/analyze action allowed in `READ_ONLY` mode.
- Raw spool output is never stored in audit logs.
- Direct FastAPI endpoint calls skip Django session audit logging; the audited
  path is the Django UI/API proxy.

See `docs/ai-safety.md` for the safety model and `docs/demo-ai-spool-explanation.md`
for a hands-on demo flow.