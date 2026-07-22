#!/usr/bin/env bash
# z-agent DevOps API example: job summary (v0.5.0)
#
# All values are FAKE. Replace ZAGENT_URL and IBM Z headers with your own
# non-production values. Do not hardcode real credentials in this file.
set -euo pipefail

ZAGENT_URL="${ZAGENT_URL:-http://z-agent.example.org}"
JOB_ID="${JOB_ID:-JOB12345}"
JOB_NAME="${JOB_NAME:-PAYROLL01}"

# IBM Z credentials are passed only via headers / env, never hardcoded.
ZOWE_HOST="${ZOWE_HOST:-demo.example.org}"
ZOWE_PORT="${ZOWE_PORT:-10443}"
ZOWE_USER="${ZOWE_USER:-TESTUSR}"
ZOWE_PASSWORD="${ZOWE_PASSWORD:-}"  # leave empty; set via env

echo "Calling z-agent job summary API for ${JOB_ID} (${JOB_NAME})..."

curl -s -X POST "${ZAGENT_URL}/api/devops/job-summary" \
  -H "Content-Type: application/json" \
  -H "X-Zowe-Host: ${ZOWE_HOST}" \
  -H "X-Zowe-Port: ${ZOWE_PORT}" \
  -H "X-Zowe-User: ${ZOWE_USER}" \
  -H "X-Zowe-Password: ${ZOWE_PASSWORD}" \
  -d "{
    \"job_id\": \"${JOB_ID}\",
    \"job_name\": \"${JOB_NAME}\",
    \"include_ai_explanation\": true
  }" | python -m json.tool