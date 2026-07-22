# Demo Script

> z-agent does not replace Zowe. It uses Zowe/zOSMF as the access layer and adds
> AI-assisted operations, safety modes, and auditability on top.

This is a 3–5 minute narrated demo for Open Mainframe/Zowe reviewers.

Before the demo: start z-agent (Docker Compose or local) with a non-production
IBM Z connection and a local Ollama model pulled (e.g. `llama3.2:3b`). Do not
use production credentials or real spool data.

## Step 1 — Positioning (30s)

Open the README and point to the architecture diagram.

> Narration: "z-agent does not replace Zowe. It uses Zowe/zOSMF as the access
> layer and adds AI-assisted operations, safety modes, and auditability on
> top. The goal is to turn hard-to-read IBM Z spool output into structured,
> masked, audited explanations for operators, developers, and pipelines."

## Step 2 — Setup page / AI settings (30s)

Open the setup page.

> Narration: "Users enter their own non-production IBM Z credentials here.
> Credentials live only in the web session — nothing is baked into the image.
> On the same page we pick the AI provider; we default to a local Ollama model
> so spool data does not leave the lab."

## Step 3 — Jobs dashboard (20s)

Open the jobs dashboard.

> Narration: "Jobs come straight from Zowe/zOSMF. z-agent classifies return
> codes so failures jump out immediately."

## Step 4 — Spool viewer (30s)

Open a failed job's spool.

> Narration: "The spool viewer shows JESMSGLG, JESJCL, and JESYSMSG sections.
> Python already extracted the facts — return code, ABEND, and the evidence
> lines. Python decides the facts; AI explains the facts."

## Step 5 — Explain with AI (45s)

Click **Explain with AI**.

> Narration: "Before anything goes to the model, z-agent masks sensitive
> values — dataset names, passwords, IPs, emails — so raw secrets never reach
> the AI. The model then returns a strict JSON object."

## Step 6 — Structured explanation (30s)

Show the result panel.

> Narration: "We get likely cause, evidence from the spool, a suggested next
> step, a confidence level, the model used, and an audit ID. If Ollama is
> down, we get a safe error instead of a crash."

## Step 7 — Audit log (30s)

Open the Audit Logs page.

> Narration: "Every AI explanation is logged as AI_EXPLAIN_SPOOL with metadata
> only — timestamp, user, job ID, model, safety mode, status. The raw spool is
> never stored in the audit log."

## Step 8 — DevOps API (45s)

Open a terminal and run the curl example (dry-run safe).

> Narration: "Pipelines don't need a web session. They call the job-summary
> API with headers and get a structured JSON response. The key field for CI/CD
> is `safe_to_continue` — the pipeline can gate on it. Incident summaries and
> dry-run webhook notifications are available too, all audit-logged."

```bash
# Fake values only
curl -s -X POST http://z-agent.example.org/api/devops/job-summary \
  -H "Content-Type: application/json" \
  -d '{"job_id":"JOB12345","job_name":"PAYROLL01","include_ai_explanation":true}'
```

## Step 9 — Safety modes and docs (30s)

Open the safety settings page and `docs/ai-safety.md`.

> Narration: "AI explanation is a read/analyze action, allowed in READ_ONLY.
> JCL submit is risky — it requires approval or EXECUTE mode. Real webhook
> sends are also gated. This is what makes z-agent an operations tool, not
> just a learning demo."

## Step 10 — Open Mainframe alignment (15s)

Open `docs/open-mainframe-alignment.md`.

> Narration: "z-agent builds on Zowe, stays open source and local-first, and
> targets the gap between Zowe access and enterprise AIOps. It is not
> production-ready yet — we want community feedback and testers."

## Closing line

> "Zowe gives access. z-agent adds guidance."