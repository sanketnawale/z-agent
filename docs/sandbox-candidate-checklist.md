# Sandbox Candidate Checklist

> z-agent does not replace Zowe. It builds on Zowe/zOSMF.

This checklist tracks z-agent's readiness for Open Mainframe/Zowe community
feedback and future Sandbox discussion. It is **honest** — unfinished items are
unchecked. This is a draft candidate package, not a formal Open Mainframe
acceptance.

## Project identity

- [x] Public repository
- [x] Apache-2.0 LICENSE
- [x] README with clear project positioning
- [x] CONTRIBUTING.md
- [x] SECURITY.md
- [x] CHANGELOG.md
- [x] ROADMAP.md
- [x] GOVERNANCE.md
- [x] MAINTAINERS.md
- [x] TESTERS.md

## Open Mainframe alignment

- [x] docs/open-mainframe-alignment.md
- [x] docs/sandbox-proposal-draft.md
- [x] docs/project-pitch.md (v0.6.0)
- [x] docs/landscape.md
- [x] docs/use-cases.md
- [x] docs/faq.md (v0.6.0)
- [ ] Formal Open Mainframe Project Sandbox submission (not started)

## Zowe relationship

- [x] docs/comparison-with-zowe.md
- [x] Zowe CLI used as the access layer for all z/OS operations
- [x] Documented positioning: z-agent builds on Zowe, does not replace it
- [x] Future Zowe MCP integration noted in roadmap

## Current features

- [x] Browser-based IBM Z setup page with session profiles
- [x] Django frontend and FastAPI backend
- [x] Zowe CLI integration (jobs, spool, datasets, USS, JCL)
- [x] Jobs dashboard and spool viewer
- [x] Rule-based spool diagnosis (return codes, ABENDs, message codes)
- [x] AI-assisted spool explanation via pluggable AI gateway
- [x] Dataset Explorer and member viewer
- [x] USS browser
- [x] JCL submit with approval gating
- [x] AI provider and model switching (rule-based, Ollama, Claude, OpenAI, Gemini)
- [x] Docker Compose deployment with local Ollama

## Safety and audit

- [x] Safety modes: READ_ONLY, APPROVAL_REQUIRED, EXECUTE
- [x] Audit logging for read and write actions
- [x] JCL submit gated by safety mode and approval
- [x] docs/security-model.md
- [x] docs/security-review-checklist.md (v0.6.0)

## AI safety

- [x] Sensitive data masking before AI analysis (agent/masking.py)
- [x] Constrained prompt forbidding destructive actions (agent/prompts.py)
- [x] Safe error responses — raw exceptions never exposed to users
- [x] AI explanation is a read-only action (allowed in READ_ONLY)
- [x] docs/ai-operations.md
- [x] docs/ai-safety.md
- [x] docs/demo-ai-spool-explanation.md

## DevOps integration

- [x] POST /api/devops/job-summary
- [x] POST /api/devops/incident-summary
- [x] POST /api/devops/notify (dry-run by default)
- [x] Ownership routing example (examples/config/ownership-rules.example.yaml)
- [x] examples/jenkins/Jenkinsfile.z-agent-example
- [x] examples/github-actions/z-agent-mainframe-job-check.yml
- [x] examples/api/*.sh curl examples
- [x] docs/devops-integration.md
- [x] docs/pipeline-examples.md
- [x] docs/incident-routing.md

## Documentation

- [x] docs/architecture.md (v0.6.0)
- [x] docs/demo-script.md (v0.6.0)
- [x] docs/demo.md
- [x] docs/setup.md
- [x] docs/known-limitations.md (v0.6.0)
- [x] docs/release-checklist.md (v0.6.0)
- [x] docs/good-first-issues.md (v0.6.0)
- [x] docs/zowe-integration.md
- [x] .github/ISSUE_TEMPLATE + pull_request_template + CODEOWNERS

## Governance

- [x] Maintainer-led project with public issue/PR discussion
- [x] Security reports handled privately (SECURITY.md)
- [x] Major changes start as GitHub Issues
- [ ] Multiple maintainers (only one today)
- [ ] Maintainer council (future)
- [ ] Contributor ladder (future)

## Community readiness

- [x] Public repo and docs
- [x] GitHub issue/PR templates
- [x] TESTERS.md with safe testing guidance
- [x] Sandbox proposal draft
- [ ] External testers (in progress)
- [ ] Community demo/events (future)
- [ ] Production adoption (not yet)

## Testing

- [x] Tests for safety modes
- [x] Tests for masking utility
- [x] Tests for prompt builder
- [x] Tests for Ollama service (success + failure)
- [x] Tests for explain-spool endpoint + audit
- [x] Tests for DevOps endpoints + audit + dry-run
- [x] Tests asserting examples contain no real secrets
- [x] Tests asserting raw spool not stored in audit logs

## Known limitations

- [x] docs/known-limitations.md (v0.6.0)
- [ ] Not production-ready (honest)
- [ ] No SLA / production support

## Next 6-month roadmap

- [ ] Recruit external testers
- [ ] Add maintainers
- [ ] More spool diagnosis patterns
- [ ] Kubernetes / Helm deployment
- [ ] OpenTelemetry-friendly observability
- [ ] SMF analytics behind authorized access + safety model
- [ ] GitLab CI / Azure DevOps examples
- [ ] Job lifecycle automation

## Summary

z-agent has the documentation, safety, audit, AI, and DevOps building blocks for
a Sandbox candidate package. The two biggest open items are **external
testers** and **multiple maintainers** — both are community-growth goals, not
code goals.