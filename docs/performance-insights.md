# Performance Insights

> The v0.7.0 Performance Insights Preview calculates ratios from provided
> statistical data and uses local/demo thresholds. It does not claim to
> compare against an external benchmark population unless an authorized
> benchmark dataset is configured in a future version.

> z-agent does not replace Zowe. It builds on Zowe/zOSMF.

## What Performance Insights is

Performance Insights is a z-agent preview module that calculates mainframe
efficiency ratios from *provided statistical metrics* and assigns a grade
based on a standard-deviation ratio scale concept. It optionally produces an
advisory AI explanation of the report.

This is **not** full SMF/RMF production analytics. It is a preview that accepts
sample/manual/statistical input through an API and a simple UI.

The workflow:

```text
statistical metrics input
  -> calculate ratio values
  -> assign scale grade
  -> estimate improvement opportunity
  -> generate AI-readable explanation (optional)
  -> create audit log metadata
  -> show result via API/UI/docs
```

## Scale / grade concept (neutral summary)

The preview is inspired by a standard-deviation ratio scale concept provided
for the project. The scale maps a score to a grade:

```text
score <= -3 -> F   (severe underperformance)
score == -2 -> E   (may save about 12%)
score == -1 -> D   (may save about 9%)
score ==  0 -> AVG (average; between -1 and +1 is average)
score == +1 -> C   (may save about 6%)
score == +2 -> B   (may save about 3%)
score >= +3 -> A   (about perfect)
```

### Local/demo thresholds (preview)

For the v0.7 preview, exact standard-deviation comparison data is unavailable.
z-agent uses deterministic, documented **preview local thresholds** to map each
ratio's numeric value to a -3..+3 score. These thresholds are **not** marketed
as real industry benchmarks. See `docs/performance-ratios.md` for the threshold
bands.

> The v0.7 preview uses local/demo thresholds. Real standard deviation
> benchmarking requires an authorized benchmark dataset.

## API

```text
POST /api/performance/insights
```

Request:

```json
{
  "system_name": "demo-lpar",
  "period": "2026-07-demo",
  "metrics": {
    "cpu_time_used": 7200,
    "total_cpu_capacity": 14400,
    "online_cpu_time_used": 2500,
    "total_transactions": 100000,
    "batch_cpu_time_used": 4700,
    "batch_jobs_completed": 1200,
    "total_batch_window_minutes": 360,
    "io_operations": 850000,
    "workload_processed": 500000,
    "cost": 1200
  },
  "include_ai_explanation": true
}
```

Response (abbreviated):

```json
{
  "system_name": "demo-lpar",
  "period": "2026-07-demo",
  "overall_grade": "C",
  "overall_score": 1,
  "benchmark_mode": "local-scale-only",
  "ratios": [ ... ],
  "ai_explanation": { "available": true, "summary": "...", "safe_next_steps": [] },
  "audit_id": "AUD-000456",
  "disclaimer": "..."
}
```

If AI is unavailable, the response still returns ratio results without crashing:

```json
{
  "ai_explanation": {
    "available": false,
    "message": "AI explanation unavailable. Ratio calculations returned without AI explanation."
  }
}
```

## UI

Open the **Performance Insights** page (`/performance/`) and paste metrics
JSON, then click **Analyze Performance**. The result panel shows the overall
grade, a ratio table, the AI explanation (if available), the audit ID, the
benchmark mode, and the disclaimer.

## Audit

Each analysis creates a `PERFORMANCE_INSIGHTS_ANALYSIS` audit log entry with
metadata only — system name, period, ratio names calculated, AI used, and
benchmark mode. **Raw metrics are never stored in audit logs.**

## Safety

- Performance analysis is a **read/analyze** action and is allowed in every
  safety mode, including `READ_ONLY`.
- It does not install programs and does not modify anything on IBM Z.
- AI output is **advisory only**.
- Examples use synthetic data only.

See `docs/performance-ratios.md` for ratio formulas and thresholds, and
`docs/performance-data-handling.md` for data safety rules.

## Future

- Authorized SMF/RMF data source integration.
- Authorized benchmark dataset support (real standard-deviation comparison).
- More ratios and configurable thresholds.

z-agent does **not** claim to compare against "600 mainframes" or any external
population unless an authorized benchmark dataset is configured in a future
version.