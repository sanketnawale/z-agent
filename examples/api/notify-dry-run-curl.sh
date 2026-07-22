#!/usr/bin/env bash
# z-agent DevOps API example: webhook notify dry-run (v0.5.0)
#
# All values are FAKE. dry_run defaults to true so no network request is sent.
# Do not use real webhook URLs or real tokens in this file.
set -euo pipefail

ZAGENT_URL="${ZAGENT_URL:-http://z-agent.example.org}"
JOB_ID="${JOB_ID:-JOB12345}"
JOB_NAME="${JOB_NAME:-PAYROLL01}"
WEBHOOK_URL="${WEBHOOK_URL:-https://example.org/webhook}"

echo "Calling z-agent notify API in dry-run mode for ${JOB_ID}..."

curl -s -X POST "${ZAGENT_URL}/api/devops/notify" \
  -H "Content-Type: application/json" \
  -d "{
    \"webhook_url\": \"${WEBHOOK_URL}\",
    \"job_id\": \"${JOB_ID}\",
    \"job_name\": \"${JOB_NAME}\",
    \"summary\": \"Job failed with RC=12\",
    \"dry_run\": true
  }" | python -m json.tool