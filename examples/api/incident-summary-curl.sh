#!/usr/bin/env bash
# z-agent DevOps API example: incident summary (v0.5.0)
#
# All values are FAKE. Replace ZAGENT_URL and IBM Z headers with your own
# non-production values. Do not hardcode real credentials in this file.
set -euo pipefail

ZAGENT_URL="${ZAGENT_URL:-http://z-agent.example.org}"
JOB_ID="${JOB_ID:-JOB12345}"
JOB_NAME="${JOB_NAME:-PAYROLL01}"

# FAKE sample spool text - do not use real production spool output.
SPOOL_TEXT=$(cat <<'EOF'
$HASP395 PAYROLL01 ENDED - RC=0012
Spool file:  JESMSGLG
IEFC621D ALLOCATION FAILED FOR USER01.PAYROLL.PROD.INPUT
IEFC660E
Spool file:  JESYSMSG
Spool file:  JESJCL
EOF
)

ZOWE_HOST="${ZOWE_HOST:-demo.example.org}"
ZOWE_PORT="${ZOWE_PORT:-10443}"
ZOWE_USER="${ZOWE_USER:-TESTUSR}"
ZOWE_PASSWORD="${ZOWE_PASSWORD:-}"

echo "Generating incident summary for ${JOB_ID} (${JOB_NAME})..."

curl -s -X POST "${ZAGENT_URL}/api/devops/incident-summary" \
  -H "Content-Type: application/json" \
  -H "X-Zowe-Host: ${ZOWE_HOST}" \
  -H "X-Zowe-Port: ${ZOWE_PORT}" \
  -H "X-Zowe-User: ${ZOWE_USER}" \
  -H "X-Zowe-Password: ${ZOWE_PASSWORD}" \
  -d "$(python -c "import json,sys; print(json.dumps({
    'job_id': '${JOB_ID}',
    'job_name': '${JOB_NAME}',
    'spool_text': sys.stdin.read(),
    'include_ai_explanation': True
  }))" <<< "${SPOOL_TEXT}")" | python -m json.tool