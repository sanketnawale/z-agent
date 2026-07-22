# Testers and Early Adopters

z-agent is looking for **early testers** to try the project on safe,
non-production systems and give feedback. This file explains who is a good fit,
what to test, what not to share, how to report feedback, and suggested test
scenarios.

> z-agent does not replace Zowe. It builds on Zowe/zOSMF.

## Who should test

z-agent is best tested by people working with **non-production** IBM Z systems:

- IBM Z learners and students
- Zowe users who already have a z/OSMF test connection
- Mainframe developers on dev/test LPARs
- DevOps engineers working on non-production hybrid pipelines
- Operations teams evaluating tools against non-production systems

We explicitly welcome first-time contributors and reviewers. See
`docs/good-first-issues.md` for beginner-friendly ways to help.

## What to test

- Setup page and IBM Z connection flow
- Jobs dashboard and spool viewer
- AI-assisted spool explanation ("Explain with AI")
- Sensitive-data masking before AI analysis
- Dataset Explorer and member explanation
- USS browser
- Safety modes and audit logs
- JCL submit approval flow (in `APPROVAL_REQUIRED` / `EXECUTE` modes)
- Local Ollama integration
- DevOps APIs (`/api/devops/job-summary`, `/api/devops/incident-summary`,
  `/api/devops/notify` with `dry_run: true`)

## What not to share

z-agent never asks you to share sensitive data. When testing:

- **Do not share production credentials.**
- **Do not paste real company spool output** into issues or feedback.
- **Do not share private hostnames, tokens, or certificates.**
- **Do not provide real SMF records** to any community channel.
- **Do not commit** `.env`, `zowe.config.json`, `db.sqlite3`, or any
  credentials. They are gitignored for this reason.
- If you are uncertain whether something is sensitive, treat it as sensitive and
  do not share it.

## How to report feedback

- Open a **GitHub Issue** using the bug report or feature request templates
  (`.github/ISSUE_TEMPLATE/`).
- Describe what you did, what you expected, and what happened — **without
  secrets**.
- For security issues, follow `SECURITY.md` and report **privately** to the
  maintainer; do not open a public issue with sensitive details.

## Suggested test scenarios

A good first review pass covers these scenarios in order:

1. **Run local setup** — `docker compose up -d --build`, open
   `http://localhost:8001`, complete the setup page with a non-production
   connection.
2. **Review the README** — confirm the positioning ("builds on Zowe, does not
   replace it") is clear.
3. **Try AI spool explanation with sample/masked spool** — open a failed job,
   click **Explain with AI**, and verify you get a structured result with likely
   cause, evidence, suggested next step, confidence, and audit ID.
4. **Review DevOps API examples** — run `examples/api/job-summary-curl.sh`
   (with fake values) and confirm the JSON shape matches `docs/devops-integration.md`.
5. **Review safety modes** — set `READ_ONLY` and confirm JCL submit and real
   webhook sends are blocked; confirm AI explanation still works.
6. **Review audit behavior** — open the Audit Logs page and confirm a
   `DEVOPS_JOB_SUMMARY` or `AI_EXPLAIN_SPOOL` entry exists with metadata only
   (no raw spool text).
7. **Review Zowe alignment docs** — read `docs/comparison-with-zowe.md` and
   `docs/open-mainframe-alignment.md` and tell us if the positioning lands.

## What we do with feedback

- Issues are discussed publicly and prioritized by maintainers (see
  `GOVERNANCE.md`).
- Docs, tests, and safety improvements are prioritized based on tester input.
- Tester reports help move z-agent toward Open Mainframe Project Sandbox
  readiness (see `docs/sandbox-proposal-draft.md`).

Do not ask for production credentials or production data — we will never
request them.

Thank you for helping z-agent grow responsibly.