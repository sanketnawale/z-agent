# Testers and Early Adopters

z-agent is looking for **early testers** to try the project on safe,
non-production systems and give feedback. This file explains who is a good fit
and how to help safely.

## Who is a suitable tester

z-agent is best tested by people working with **non-production** IBM Z systems:

- IBM Z learners and students
- Zowe users who already have a z/OSMF test connection
- Mainframe developers on dev/test LPARs
- DevOps engineers working on non-production hybrid pipelines
- Operations teams evaluating tools against non-production systems

## Important safety rules for testers

z-agent never asks you to share sensitive data. When testing:

- **Do not share production credentials**.
- **Do not paste real company spool output** into issues or feedback.
- **Do not share private hostnames, tokens, or certificates**.
- **Do not provide real SMF records** to any community channel.
- Use the setup page with your own test-system credentials only; do not commit
  `.env` or `zowe.config.json` (they are gitignored for this reason).

If you are uncertain whether something is sensitive, treat it as sensitive and
do not share it.

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

## How to give feedback

- Open a **GitHub Issue** using the bug report or feature request templates.
- Describe what you did, what you expected, and what happened — without secrets.
- If you find a security issue, follow `SECURITY.md` and report it
  **privately** to the maintainer; do not open a public issue with sensitive
  details.

## What we do with feedback

- Issues are discussed publicly and prioritized by maintainers (see
  `GOVERNANCE.md`).
- Docs, tests, and safety improvements are prioritized based on tester input.
- Tester reports help move z-agent toward Open Mainframe Project Sandbox
  readiness (see `docs/sandbox-proposal-draft.md`).

Thank you for helping z-agent grow responsibly.