# Pipeline Examples

> Do not use production IBM Z credentials, real spool output, private SMF
> data, or company-sensitive data in public examples or issues.

This document points to ready-to-adapt pipeline examples that call z-agent's
DevOps APIs.

## Jenkins

See `examples/jenkins/Jenkinsfile.z-agent-example`.

The pipeline:

1. Calls `POST /api/devops/job-summary` via `curl`.
2. Parses the JSON response.
3. Prints likely cause, suggested next step, return code, and audit ID.
4. Fails the pipeline when `safe_to_continue` is `false`.

Fake values are used for the URL/token; real values are stored in Jenkins
credentials (`credentials('zagent-token')`, etc.).

## GitHub Actions

See `examples/github-actions/z-agent-mainframe-job-check.yml`.

The workflow:

1. Calls `POST /api/devops/job-summary` using `curl`.
2. Stores and parses the response with Python.
3. Writes a job summary to the GitHub Actions summary.
4. Fails the workflow when `safe_to_continue` is `false` (sets `::error::`).

URLs and tokens are placeholders (`${{ secrets.ZAGENT_URL }}`).

## curl examples

- `examples/api/job-summary-curl.sh`
- `examples/api/incident-summary-curl.sh`
- `examples/api/notify-dry-run-curl.sh`

Each script uses fake data and safe defaults. The notify example defaults to
`dry_run: true` so no network request is sent.

## Response cheat-sheet

| Endpoint | Key fields |
| --- | --- |
| `POST /api/devops/job-summary` | `status`, `return_code`, `safe_to_continue`, `likely_cause`, `suggested_next_step`, `audit_id` |
| `POST /api/devops/incident-summary` | `title`, `severity`, `summary`, `recommended_owner`, `suggested_next_step`, `audit_id` |
| `POST /api/devops/notify` | `status` (`dry_run`/`sent`/`error`), `payload`, `audit_id` |

See `docs/devops-integration.md` for the full API reference and
`docs/incident-routing.md` for ownership routing.