# Project Pitch

> z-agent does not replace Zowe. It builds on Zowe/zOSMF to provide a safe,
> auditable, AI-assisted operations layer for IBM Z.

This is a concise, one-page explanation for Open Mainframe/Zowe reviewers.

## What is z-agent?

z-agent is an open-source, AI-assisted IBM Z operations platform for hybrid
mainframe environments. It provides a Django web UI and REST API on top of
Zowe/zOSMF, with a pluggable AI gateway that defaults to a local Ollama model.

## Problem

Mainframe job output is hard to read: JES messages, JCL errors, COBOL compiler
messages, ABENDs, return codes, and long spool sections. Today, teams manually
search spool output or escalate to senior mainframers — slow and a bottleneck
for onboarding, support, and DevOps.

Existing open-source tools give **access** (Zowe) and **IDE** experiences (Zowe
Explorer), but there is no open-source, local-first **operations layer** that
adds structured AI explanation, safety modes, and audit logging on top of z/OS
access without sending raw sensitive data to the cloud.

## Solution

z-agent turns the spool output into structured, masked, audited AI
explanations and pipeline-friendly JSON:

```
IBM Z job spool output
  -> sensitive data masking
  -> local Ollama AI explanation
  -> structured result
  -> audit log entry
  -> UI/API result
```

## Why now?

- Hybrid mainframe teams need **advisory AI** that is local-first and
  auditable, not another cloud SaaS that ingests sensitive spool data.
- Zowe has matured into a stable access foundation; the natural next step is a
  safe operations layer on top.
- The Open Mainframe Project is growing community tooling — an open-source,
  local-first operations assistant fills a real gap.

## Why Open Mainframe?

- Grows mainframe skills and accessibility (onboarding, junior developers).
- Builds on OMP/IBM standards (Zowe, z/OSMF) rather than reinventing access.
- Open source (Apache-2.0), safety-first, audit-first — aligned with
  responsible operations.
- Targets a concrete gap: open-source local-first IBM Z operations layer with
  AI assistance, safety, and audit logging.

## Relationship with Zowe

Zowe provides access and framework. z-agent provides AI-assisted operations
workflows, safety modes, audit logs, and a Django UI/API **on top** of Zowe.

| Layer | Provided by | Role |
| --- | --- | --- |
| z/OS access, APIs, profiles | Zowe CLI / z/OSMF | Foundation |
| Desktop, Explorer, MCP | Zowe | Frameworks and clients |
| AI ops, safety, audit, UI/API | z-agent | Operations layer |

z-agent depends on Zowe CLI for every z/OS operation. It does not duplicate
Zowe's access role.

## Current features

- Jobs/spool/datasets/USS browsing and JCL submit (via Zowe)
- Rule-based spool diagnosis
- AI-assisted, masked spool explanation (local Ollama default)
- Safety modes (READ_ONLY, APPROVAL_REQUIRED, EXECUTE)
- Audit logging for read and write actions
- Pipeline APIs: job summary, incident summary, dry-run webhook notify
- Jenkins / GitHub Actions / curl examples
- Docker Compose deployment
- Performance Insights preview: ratio analysis from provided statistical metrics with advisory AI explanation (local/demo thresholds only — not a benchmark comparison)

## What makes it different

1. **Local-first AI**: defaults to Ollama so spool data does not leave the lab.
2. **Safety and audit first**: safety modes and audit logging are first-class,
   not afterthoughts.
3. **Pipeline-friendly**: structured JSON with `safe_to_continue` so CI/CD can
   act on IBM Z job results.
4. **Strictly complementary to Zowe**: it never tries to replace Zowe's
   access role.

## Demo flow

1. Setup page + AI settings
2. Jobs dashboard
3. Spool viewer → **Explain with AI**
4. Structured explanation (likely cause, evidence, next step, confidence,
   audit ID)
5. Audit log
6. DevOps job-summary curl example
7. Safety modes docs

See `docs/demo-script.md` for a full narrated 3–5 minute demo.

## Current status

- v0.1.0 public preview → v0.5.0 DevOps integration preview complete
- v0.6.0 Sandbox candidate package complete
- v0.7.0 Performance Insights preview (this milestone)
- Not production-ready
- Single maintainer today; community growth is a goal
- 90+ tests passing

## What feedback we want

- Does the project positioning land clearly (builds on Zowe, not replaces it)?
- Is the safety/audit model convincing for an operations tool?
- Are the DevOps APIs the right shape for your pipelines?
- Would your team trial z-agent on a non-production system? What's missing?
- Are there Zowe/Zowe MCP integration paths we should pursue?