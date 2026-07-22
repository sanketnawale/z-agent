# Changelog

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
