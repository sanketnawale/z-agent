# Z-Agent Demo Mode

Z-Agent Demo Mode is a way for reviewers (Forge26, Open Mainframe Project,
new contributors, and instructors) to understand what Z-Agent does **without**
needing real IBM Z credentials, a z/OSMF endpoint, or a live mainframe.

This document is the foundation of the demo mode planned in the
`v1.2.0 – Production Readiness Preview`. A later milestone may wire demo mode
into the setup page as a one-click "Try the demo" entry point.

## Goal

Let a reviewer:

1. Visit the Z-Agent web app.
2. See a representative IBM Z job lifecycle end-to-end.
3. Understand the diagnosis and AI explanation flow.
4. Understand the audit/safety layer.
5. Leave with an accurate mental model of the project — without any
   production data, credentials, or risk.

## What is in the demo (v1.2.0 foundation)

The repository ships synthetic, safe sample data that mirrors the real
end-to-end shape of Z-Agent output:

- `examples/demo-spool-output.txt` — a synthetic IBM Z job spool containing
  JESMSGLG, JESJCL, JESYSMSG, and a step SYSPRINT section. All sensitive
  values are already masked (`<DATASET_NAME>`, `<HOSTNAME_REDACTED>`,
  `<ACCOUNT_ID>`, `<USERID>`).
- `examples/demo-job-summary.json` — synthetic output mirroring the shape
  of `POST /api/devops/job-summary` (status, return code, likely cause,
  evidence, suggested next step, confidence, `safe_to_continue`, audit_id).

These files are safe to render in the web UI, copy into a slide deck, or
share with reviewers.

## Safety rules for demo data

- Demo spool output must contain **no real hostnames, IPs, accounts, or
  dataset names**. Use the same masking placeholders that
  `agent/masking.py` produces (`<DATASET_NAME>`, `<IP_ADDRESS>`,
  `<HOSTNAME_REDACTED>`, `<ACCOUNT_ID>`, `<USERID>`).
- Demo job summaries must not reference real customers, real job IDs, or
  real owners.
- Demo data must never be ingested into the audit log as if it were a
  real action — when demo mode is later wired into the UI, audit entries
  must record `DEMO_*` action types and still never store raw secrets.

## How a reviewer can use the demo today

Even before demo mode is wired into the UI, a reviewer can:

1. Read `examples/demo-spool-output.txt` to see what real IBM Z spool
   output looks like and what Z-Agent parses.
2. Read `examples/demo-job-summary.json` to see the structured summary
   that the DevOps API returns.
3. Inspect `agent/masking.py` and `agent/devops.py` to see how the
   structured summary is produced and how secrets are scrubbed.
4. Run the app locally with `docker compose up -d --build` and exercise
   `/api/health` to confirm the stack is alive.

## Future demo mode (beyond v1.2.0)

- A "Try the demo" button on the setup page that loads the demo job
  instead of asking for IBM Z credentials.
- A read-only demo dataset explorer backed by `examples/demo-*` files.
- A demo DevOps pipeline (`examples/jenkins`/
  `examples/github-actions`) that posts the demo job summary to a
  webhook in dry-run mode.
- Demo audit log entries seeded with `DEMO_*` action types.

## Related files

- `examples/demo-spool-output.txt`
- `examples/demo-job-summary.json`
- `docs/demo.md`
- `docs/demo-script.md`
- `docs/demo-ai-spool-explanation.md`
- `docs/v1.2-production-readiness-plan.md`
- `agent/masking.py`
- `agent/devops.py`