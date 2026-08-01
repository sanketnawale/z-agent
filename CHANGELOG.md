# Changelog

## [v1.2.0-production-readiness-preview] - Unreleased

### Added
- Production readiness plan (`docs/v1.2-production-readiness-plan.md`)
- Versioned health endpoints
  - FastAPI `GET /api/health` (with `service` and `version`) — `/health` kept for backward compatibility
  - Django `GET /api/health`
- Environment-based Django settings
  - `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DJANGO_SECRET_KEY`
  - `SECURE_PROXY_SSL_HEADER` for reverse-proxy HTTPS
- Docker Compose production readiness
  - `healthcheck` against `/api/health` for the web container
  - Production environment block (DEBUG=false, real allowed hosts, env SECRET_KEY)
- Expanded `.env.example` with safe defaults for the new env vars and AI provider/model
- Production deployment documentation (`docs/production-deployment.md`)
  including Nginx + Let's Encrypt example and health endpoint reference
- Demo mode foundation
  - `examples/demo-spool-output.txt` (synthetic, pre-masked IBM Z spool)
  - `examples/demo-job-summary.json` (synthetic DevOps job summary)
  - `docs/demo-mode.md`
- README screenshots for Performance Insights and Safety Settings

### Security
- No credentials, spool output, or dataset names committed
- Demo spool content is masked and synthetic — no real hostnames/accounts
- `DJANGO_SECRET_KEY` now sourced from env with a dev-only placeholder default
- `DJANGO_DEBUG` defaults to `true` only for local dev; Docker Compose sets it to `false`

### Notes
- This release prepares Z-Agent for the Forge26 and Open Mainframe review.
- It does not add risky features: no automatic job submit/kill, no DB-stored
  credentials, no AI-decided actions, and no public demo against real IBM Z.

## [v0.7.0-performance-insights-preview] - Unreleased

### Added
- Performance Insights preview module
- Ratio calculation engine
- Standard deviation ratio scale mapping
- Performance insights API endpoint
- Optional AI explanation for performance ratio reports
- Performance Insights UI page
- Performance analysis audit action
- Synthetic performance metrics example
- Performance Insights curl example
- Performance Insights documentation
- Performance ratio documentation
- Performance data-handling documentation

### Safety
- Uses synthetic/sample metrics only in examples
- Does not store raw metric files in audit logs
- Does not claim external benchmark comparison without authorized benchmark data
- Performance analysis is advisory only

## [v0.6.0-sandbox-candidate] - Unreleased

### Added
- Sandbox candidate checklist
- Project pitch one-pager
- Demo script
- Architecture overview
- Known limitations document
- Release checklist
- Security review checklist
- Improved tester guidance
- Good first issues guide
- FAQ
- README links to Sandbox candidate materials

### Notes
- This milestone prepares z-agent for Open Mainframe/Zowe community feedback.
- It does not claim production readiness or formal Open Mainframe acceptance.

## [v0.5.0-devops-integration-preview] - Unreleased

### Added
- Pipeline-friendly job summary API
- Incident summary API
- Ownership routing example
- Webhook notification dry-run support
- DevOps audit action types
- Jenkins pipeline example
- GitHub Actions example
- API curl examples
- DevOps integration documentation
- Pipeline examples documentation
- Incident routing documentation

### Security
- Webhook notification defaults to dry-run mode
- Raw spool output is not stored in audit logs
- Examples use fake URLs, fake tokens, and placeholder secrets only

## [v0.4.0-open-mainframe-readiness] - Unreleased

### Added
- Open Mainframe alignment documentation (docs/open-mainframe-alignment.md)
- Zowe comparison documentation (docs/comparison-with-zowe.md)
- Landscape analysis (docs/landscape.md)
- Use cases documentation (docs/use-cases.md)
- Sandbox proposal draft (docs/sandbox-proposal-draft.md)
- Project governance (GOVERNANCE.md)
- Maintainers file (MAINTAINERS.md)
- Testers / early adopters file (TESTERS.md)
- GitHub community files: bug report and feature request issue templates
- GitHub pull request template
- CODEOWNERS file
- README Open Mainframe Alignment section

### Changed
- Populated empty docs/open-mainframe-sandbox-readiness.md as a doc index pointer

### Notes
- This milestone is documentation, governance, and community-readiness only.
- No core application code changes beyond documentation links.
- z-agent does not replace Zowe; it builds on Zowe/zOSMF.

## [v0.3.0-ai-operations-preview] - Unreleased

### Added
- AI-assisted spool explanation workflow
- Sensitive data masking before AI analysis
- Prompt template for IBM Z spool analysis
- Audit logging for AI explanation actions
- UI action to explain spool output with AI
- Tests for masking, AI explanation, and audit behavior
- AI operations and AI safety documentation

### Security
- Raw secrets and sensitive values are masked before AI analysis
- Raw spool output is not stored in audit logs

## [v0.1.0-public-preview] - 2026-06-13

### Added
- Public project documentation
- LICENSE, CONTRIBUTING.md, SECURITY.md, ROADMAP.md, CHANGELOG.md
- Demo guide
- Screenshots for setup page, jobs dashboard, spool viewer, dataset explorer, USS browser, and AI settings
- Initial public README positioning
- Public preview release tag

### Changed
- Cleaned repository for public release
- Updated .gitignore

### Security
- Ignored local secrets and environment-specific files:
  - .env
  - zowe.config.json
  - zowe.schema.json
  - venv
  - __pycache__
  - db.sqlite3

### Notes
- This release is a public preview and is not intended for production use.
