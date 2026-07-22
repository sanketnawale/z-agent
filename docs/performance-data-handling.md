# Performance Data Handling

> The v0.7.0 Performance Insights Preview calculates ratios from provided
> statistical data and uses local/demo thresholds. It does not claim to
> compare against an external benchmark population unless an authorized
> benchmark dataset is configured in a future version.

> z-agent does not replace Zowe. It builds on Zowe/zOSMF.

This page documents how z-agent handles metrics data for the Performance
Insights preview. The principles follow the safety/data-handling idea
provided for the project.

## Core principles

- **Collect statistical data only.** z-agent accepts high-level statistical
  metrics (counts, totals, ratios), not raw logs.
- **No programs installed.** Performance Insights does not install anything on
  IBM Z. It is an analysis layer.
- **Use IBM utilities (future).** When SMF/RMF integration is added in a future
  version, z-agent will rely on IBM-provided utilities and authorized access.
- **Do not collect source code, credentials, or sensitive business data.**
  Performance Insights does not ingest source code, credentials, or
  business-sensitive content.

## What is accepted

The API accepts a JSON object of high-level statistical metrics:

```json
{
  "system_name": "demo-lpar",
  "period": "2026-07-demo",
  "metrics": { "cpu_time_used": 7200, "...": "..." }
}
```

In this preview, all example data is **synthetic**. See
`examples/performance/demo-metrics.json`.

## What is not stored

- **Raw uploaded metric values are never stored in audit logs.** Audit entries
  record metadata only: system name, period, ratio names calculated, AI used,
  benchmark mode, status.
- **Metric files are not persisted.** Metrics are used in-memory to compute
  ratios and then discarded.
- **No raw SMF/RMF records are collected** in this preview.

## Audit metadata (safe)

Each analysis writes a `PERFORMANCE_INSIGHTS_ANALYSIS` audit entry with:

- timestamp (`created_at`)
- action type (`PERFORMANCE_INSIGHTS_ANALYSIS`)
- target (`system_name`)
- safety mode
- status (`ALLOWED` / `FAILED`)
- details (period, ratio names, ai_used, benchmark_mode, metric key names
  only — **not values**)

## AI handling

When AI explanation is requested, the **structured report** (ratios, grades,
summary) is sent to the local Ollama model — not raw sensitive metrics. The
prompt forbids destructive recommendations and instructs the model to treat
output as advisory. If Ollama is unavailable, a safe error is returned and the
ratio calculations are still returned.

## Safety mode

`PERFORMANCE_INSIGHTS_ANALYSIS` is a **read/analyze** action. It is allowed in
every safety mode including `READ_ONLY` because it does not modify IBM Z and
does not install programs.

## What not to do

- Do not paste real customer SMF/RMF data into public issues or examples.
- Do not commit real benchmark datasets.
- Do not treat v0.7 thresholds as real industry benchmarks.
- Do not claim comparison against "600 mainframes" or any external population
  unless an authorized benchmark dataset is configured in a future version.

## Future

- Authorized SMF/RMF data source integration behind an explicit safety model.
- Authorized benchmark dataset support for real standard-deviation comparison.
- More ratios and configurable thresholds.