#!/usr/bin/env bash
# z-agent Performance Insights API example (v0.7.0)
#
# This is SYNTHETIC DEMO DATA. Do not commit real customer SMF/RMF data.
# All values are fake and for preview/demo only.
set -euo pipefail

ZAGENT_URL="${ZAGENT_URL:-http://z-agent.example.org}"

echo "Calling z-agent Performance Insights API with synthetic metrics..."

curl -s -X POST "${ZAGENT_URL}/api/performance/insights" \
  -H "Content-Type: application/json" \
  -d @examples/performance/demo-metrics.json | python -m json.tool