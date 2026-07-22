# Known Limitations

> z-agent does not replace Zowe. It builds on Zowe/zOSMF.

This page is an honest list of z-agent's current limitations for Open
Mainframe/Zowe reviewers and testers. z-agent is a Sandbox candidate, not a
production tool.

## Maturity

- **Not production-ready yet.** z-agent is an early public preview. It should
  not be used against production IBM Z systems without a full security review.
- **Early public preview.** The project is MVP/demo-oriented and still growing
  community.
- **No production support or SLA.** There is no vendor backing, SLA, or
  guaranteed response time today.
- **External testers are still needed.** We are actively recruiting early
  testers (see TESTERS.md). Feedback so far is maintainer-internal.

## AI

- **AI output is advisory only.** z-agent never lets AI execute actions on
  IBM Z, and it never lets AI decide job results. AI explanations may be wrong.
- **No guarantee AI explanations are correct.** Confidence is model-derived and
  should not be treated as a guarantee.
- **Masking is conservative, not a guarantee.** Sensitive values are masked
  before AI analysis, but unusual formats may occasionally slip through. Do not
  rely on masking as your only control.
- **AI availability depends on a local Ollama runtime** (or an optional cloud
  provider key). If Ollama is down, z-agent returns a safe error, not a crash.

## Access and data

- **Requires authorized IBM Z/Zowe access.** z-agent does not provide z/OS
  access itself — it depends on Zowe CLI and a reachable z/OSMF. Testers must
  use their own non-production credentials.
- **No real SMF analytics yet.** SMF telemetry is a future direction, gated on
  authorized access and an explicit safety model.
- **Performance Insights uses local/demo thresholds only.** The v0.7.0
  Performance Insights Preview calculates ratios from provided statistical
  metrics and uses local/demo thresholds. It does NOT claim external benchmark
  comparison; real benchmark comparison and SMF/RMF integration are future work.
- **No role-based access control yet.** Safety modes govern sessions, but there
  is no per-user role model today.

## Webhook and notifications

- **Webhook sending is intentionally guarded by safety mode.** Real sends
  (`dry_run: false`) are blocked in READ_ONLY and allowed only in EXECUTE (or
  APPROVAL_REQUIRED with approval). Dry-run is the default.
- **No automatic webhook fan-out from ownership rules** in the current preview.
  Use `POST /api/devops/notify` explicitly.

## Deployment

- **Kubernetes/Helm are future roadmap** unless already implemented. Today
  z-agent ships Docker Compose for local/server deployment.
- **No OpenTelemetry-friendly observability wiring yet** (roadmap).

## Community

- **Single maintainer today.** Governance is maintainer-led (GOVERNANCE.md).
  Growing maintainers and a contributor ladder are explicit goals.
- **No formal Open Mainframe acceptance.** This package is a Sandbox
  candidate draft, not a formal Open Mainframe Project Sandbox submission.

## Security posture for public channels

- **Users must not paste secrets into public issues.** Do not put production
  credentials, real spool output, private hostnames, or real SMF data into
  GitHub issues, PRs, or examples. Report security issues privately per
  SECURITY.md.
- **Direct FastAPI endpoint calls skip Django audit logging.** The audited path
  is the Django proxy, which attaches `audit_id`; calling FastAPI directly
  will not produce a session audit row.