# Open Mainframe Alignment

> z-agent does not replace Zowe. It builds on Zowe/zOSMF.

This document explains what z-agent is, why it fits the Open Mainframe
ecosystem, how it aligns with Zowe, and how it supports IBM Z operations,
onboarding, and DevOps. It is written for Open Mainframe Project community
reviewers, potential adopters, and contributors.

## What z-agent is

z-agent is an open-source, AI-assisted IBM Z operations platform for hybrid
mainframe environments. It provides a Django web UI and REST API on top of
Zowe/zOSMF, with a pluggable AI gateway that defaults to a local Ollama model.

Z-agent focuses on a single, well-scoped workflow:

```
IBM Z job spool output
  -> sensitive data masking
  -> Ollama AI explanation
  -> structured result
  -> audit log entry
  -> UI/API result
```

It is intentionally local-first and avoids sending raw sensitive data to cloud
providers. Cloud AI providers are optional and require user-provided API keys.

## Why it fits the Open Mainframe ecosystem

The Open Mainframe Project exists to grow the mainframe community, improve
tooling, and make mainframe skills more accessible. z-agent supports those goals
directly:

- **Accessibility**: a guided web UI turns hard-to-read JES/COBOL/ABEND spool
  output into clear explanations, which helps juniors, developers, and DevOps
  teams who are not deep mainframe experts.
- **Open source**: Apache-2.0 licensed, public repository, published docs, and a
  contribution guide.
- **Builds on existing OMP/IBM tooling**: z-agent does not reinvent z/OS
  access. It relies on Zowe CLI and z/OSMF, which are already community
  standards.
- **Safety and auditability**: safety modes and audit logging are first-class
  features, not afterthoughts — a key requirement for any real operations tool.
- **Local-first AI**: defaults to a local Ollama runtime so teams can explore
  AI-assisted operations without sending sensitive spool data to the cloud.

## How it aligns with Zowe

Zowe provides the access and framework. z-agent provides AI-assisted
operations workflows on top.

| Layer | Provided by | Role |
| --- | --- | --- |
| z/OS access, APIs, profiles | Zowe CLI / z/OSMF | Foundation |
| Desktop, Explorer, MCP tooling | Zowe | Frameworks and clients |
| AI-assisted operations, safety, audit, UI/API | z-agent | Operations layer |

z-agent treats Zowe as a hard dependency, not a competitor. It uses Zowe CLI to
perform jobs, spool, dataset, and USS operations, then adds:

- evidence-based Python diagnosis of spool output
- sensitive-data masking before any AI analysis
- structured AI explanations with confidence and audit IDs
- safety modes (`READ_ONLY`, `APPROVAL_REQUIRED`, `EXECUTE`)
- audit logging for read and write actions

See `docs/comparison-with-zowe.md` for a detailed component-by-component
comparison.

## How it supports IBM Z operations

z-agent covers the day-to-day operations loop for hybrid mainframe teams:

- **Jobs**: list jobs, open spool output, read return codes and ABENDs.
- **Spool intelligence**: rule-based diagnosis extracts facts; AI explains them
  in plain English.
- **JCL**: submit JCL through a safety-gated, approval-aware flow.
- **Datasets**: browse datasets and members, view content, explain members.
- **USS**: browse USS directories and files.
- **AI**: switch providers/models; use local Ollama for private analysis.

## Why it is not only a learning tool

z-agent started as an MVP/demo, but its design is operations-oriented:

- Safety modes govern what actions are allowed per session.
- Every significant action is audit-logged.
- JCL submission is gated behind approval and safety modes.
- AI analysis is read-only by design and never modifies IBM Z.
- Audit entries include metadata only — raw spool is never persisted.

These characteristics are what a real operations tool needs, not just a
teaching aid. z-agent can be used for learning *and* for assisted
troubleshooting of non-production systems today, with a path toward production
operations behind proper security review.

## How it helps operations, DevOps, support, and onboarding

- **Operations teams**: quickly triage a failed job and get a structured
  likely-cause + suggested-next-step + confidence + audit ID.
- **Developers**: understand JCL/COBOL/spool errors without paging a senior
  mainframer for every message code.
- **DevOps teams**: a REST API (`POST /api/agent/explain-spool`) is available
  to fetch a structured job-failure summary from a pipeline.
- **Support teams**: generate a consistent incident summary with evidence
  already extracted and cited.
- **Onboarding**: juniors learn by reading explanations tied to real message
  codes and evidence, rather than guessing from raw spool.

## How safety, audit, and AI fit into the project

z-agent's architecture separates concerns deliberately:

1. **Python reads the spool** and extracts factual diagnosis (return codes,
   message codes, ABENDs, evidence lines).
2. **Sensitive values are masked** before any AI call (`agent/masking.py`).
3. **A constrained prompt** instructs the model to avoid destructive actions,
   not invent facts, and return a strict JSON object (`agent/prompts.py`).
4. **A local Ollama model** produces the explanation
   (`agent/ollama_service.py`), with safe fallbacks on any failure.
5. **Every AI explanation is audit-logged** as `AI_EXPLAIN_SPOOL` with
   metadata only — never the raw spool.

AI is an advisory layer over facts Python already determined. It never decides
job results and never executes actions on IBM Z. This keeps hallucination low
and keeps the human in the loop.

See `docs/ai-safety.md` and `docs/security-model.md` for details.

## Future direction

z-agent's roadmap (see `ROADMAP.md`) is explicitly cloud-native and
community-oriented:

- **SMF telemetry**: SMF analytics behind authorized access and a safety model.
- **DevOps pipelines**: REST API usage for CI/CD job-failure summaries and
  automated triage.
- **Kubernetes / Helm**: a container-native deployment option alongside Docker
  Compose.
- **OpenTelemetry-friendly observability**: structured logs and traces for
  operations tooling.
- **ZoweX / MCP-style integration**: explore deeper Zowe ecosystem integration
  rather than parallel tooling.
- **Governance growth**: more maintainers, clearer contribution ownership, and
  community-tested releases.

## Core message

> Zowe gives access. z-agent adds guidance.
>
> z-agent does not replace Zowe. It builds on Zowe/zOSMF to provide a safe,
> auditable, AI-assisted operations layer for IBM Z and hybrid mainframe
> environments.