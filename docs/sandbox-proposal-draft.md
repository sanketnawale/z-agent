# Sandbox Proposal Draft

> **Status: DRAFT.** This is a draft Open Mainframe Project Sandbox-style
> proposal. z-agent is **not** production-ready and is presented here for
> community feedback only. Numbers and claims should be validated during
> community discussion.

## Project name

z-agent

## Short description

z-agent is an open-source, AI-assisted IBM Z operations platform for hybrid
mainframe environments. It builds on Zowe/zOSMF to provide a safe, auditable,
AI-assisted operations layer for IBM Z jobs, spool output, JCL, datasets, USS,
and (future) SMF telemetry. z-agent uses a Django web UI and REST API, with a
pluggable AI gateway that defaults to a local Ollama model.

> z-agent does not replace Zowe. It builds on Zowe/zOSMF.

## Problem statement

Mainframe job output is hard to read: JES messages, JCL errors, COBOL compiler
messages, ABENDs, return codes, and long spool sections. Today, teams manually
search spool output or escalate to senior mainframers, which is slow and a
bottleneck for onboarding and DevOps.

Existing open-source options give access (Zowe) and IDE experiences (Zowe
Explorer), but there is no open-source, local-first operations layer that adds
structured AI explanation, safety modes, and audit logging on top of z/OS access
without sending raw sensitive data to the cloud.

## Target users

- IBM Z operations teams using non-production systems
- Junior and mid-level mainframe developers
- DevOps engineers working on hybrid mainframe pipelines
- Support teams generating incident first-pass summaries
- Mainframe learners and onboarding programs
- Teams who want AI-assisted operations without a cloud/enterprise AIOps license

## Current features

- Browser-based IBM Z setup page with session-based profiles
- Django frontend and FastAPI backend
- Zowe CLI integration for jobs, spool, datasets, USS, and JCL
- Jobs dashboard and job spool viewer
- Evidence-based Python spool diagnosis (return codes, ABENDs, message codes)
- AI-assisted spool explanation via a pluggable AI gateway
- Sensitive data masking before any AI analysis
- Structured AI response: likely cause, evidence, suggested next step,
  confidence, audit ID
- Safety modes: `READ_ONLY`, `APPROVAL_REQUIRED`, `EXECUTE`
- Audit logging for read and write actions
- Dataset Explorer and member viewer
- USS browser
- JCL submit with approval gating
- AI provider and model switching (rule-based, Ollama, Claude, OpenAI, Gemini)
- Docker Compose deployment with local Ollama

## Roadmap

See `ROADMAP.md`. Highlights:

- Near term: more spool diagnosis patterns, more tests, improved API examples,
  safer JCL approval flow
- Mid term: REST API for CI/CD pipelines, job lifecycle automation, role-based
  access
- Long term: Kubernetes/Helm deployment, OpenTelemetry-friendly observability,
  ZoweX/MCP integration, SMF analytics behind authorized access and a safety
  model

## Relationship with Zowe

z-agent is a **consumer** of Zowe, not a competitor. All z/OS access in z-agent
goes through Zowe CLI and z/OSMF. z-agent adds an operations layer
(diagnosis, masking, AI explanation, safety, audit, UI/API) on top of the
access Zowe already provides.

z-agent tracks Zowe's ecosystem direction (CLI, Explorer, MCP) and intends to
remain compatible and complementary, exploring Zowe MCP as a future access
option while keeping its own safety and audit layer in control.

## Security and safety model

- No IBM Z credentials are baked into images; users enter their own on setup.
- Credentials live only in the web session; logout clears the session.
- Safety modes govern allowed actions per session; JCL submit is gated.
- AI explanation is a read/analyze action, allowed in `READ_ONLY` mode.
- Sensitive values are masked before any AI analysis; raw secrets never reach
  the model.
- Raw spool output is never stored in audit logs; only metadata is logged.
- AI explanations are advisory only and never execute actions on IBM Z.
- Local/server Ollama is the default to avoid sending data to cloud providers;
  cloud AI providers are optional and require user-provided API keys.

See `SECURITY.md`, `docs/ai-safety.md`, and `docs/security-model.md`.

## Governance status

- **Today**: maintainer-led, single maintainer. See `GOVERNANCE.md` and
  `MAINTAINERS.md`.
- **Process**: issues and PRs discussed publicly; maintainers review all
  changes; security issues follow `SECURITY.md`; major changes use GitHub Issues.
- **Goal**: grow to multiple maintainers and adopt a clearer community
  governance model as adoption grows.

## Community goals

- Recruit early testers (IBM Z learners, Zowe users, mainframe developers,
  DevOps engineers, operations teams on non-production systems). See
  `TESTERS.md`.
- Improve documentation and demo material for community review.
- Add tests for core diagnosis and AI/masking behavior.
- Stay strictly complementary to Zowe; never duplicate Zowe's access role.
- Move toward Sandbox-readiness with clear governance, docs, and a safety model.

## Why Open Mainframe Project

- z-agent directly advances OMP's mission to grow mainframe skills and tooling.
- It builds on existing OMP/IBM standards (Zowe, z/OSMF) rather than
  reinventing access.
- It is open source (Apache-2.0), local-first, and safety/audit-first — values
  aligned with responsible mainframe operations.
- It targets a real gap: an open-source, local-first IBM Z operations layer
  with AI assistance, safety, and audit logging.

## Known limitations

- Not production-ready without a full security review.
- AI explanations are advisory and may be wrong; confidence is model-derived.
- Masking is conservative, not a guarantee of complete redaction on unusual
  formats.
- No role-based access control yet.
- Direct FastAPI endpoint calls skip Django session audit logging.
- No SMF analytics yet (future work, gated on authorized access).
- Small maintainer base today.

## Next 6-month plan (indicative)

1. **Documentation & governance**: finalize alignment, comparison, and sandbox
   docs; grow maintainers and testers.
2. **Quality**: expand tests for diagnosis, masking, and API/audit behavior.
3. **Operations**: add more spool diagnosis patterns; harden JCL approval flow.
4. **DevOps**: stabilize `POST /api/agent/explain-spool` for CI/CD usage and
   publish API examples.
5. **Deployment**: add a Kubernetes/Helm deployment option.
6. **Future telemetry**: prototype masked SMF summarization behind an explicit
   safety model and authorized access.

## Draft disclaimer

This proposal is a draft intended to start community conversation. It does not
represent an accepted Sandbox project. Feedback is welcome via GitHub Issues.