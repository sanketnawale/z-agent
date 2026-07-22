# Performance Ratios

> The v0.7.0 Performance Insights Preview calculates ratios from provided
> statistical data and uses local/demo thresholds. It does not claim to
> compare against an external benchmark population unless an authorized
> benchmark dataset is configured in a future version.

> z-agent does not replace Zowe. It builds on Zowe/zOSMF.

This page documents each ratio, its formula, its preview score bands, and the
required input fields. All thresholds below are **preview local thresholds**,
not real industry benchmarks.

## Ratio

f = standard-deviation ratio scale; F = -3 → A = +3 → AVG = average/single grading.

### CPU Utilization Ratio

- **Formula**: `cpu_time_used / total_cpu_capacity`
- **Meaning**: fraction of available CPU capacity used. ~0.50 is average.
- **Preview bands** (value -> score):

| Range | Score | Grade |
| --- | --- | --- |
| <= 0.20 | -3 | F |
| <= 0.35 | -2 | E |
| <= 0.45 | -1 | D |
| <= 0.55 | 0 | AVG |
| <= 0.70 | +1 | C |
| <= 0.80 | +2 | B |
| > 0.80 | +3 | A |

### Milliseconds per Transaction Online

- **Formula**: `(online_cpu_time_used * 1000) / total_transactions`
- **Meaning**: lower is better. Uses cpu time as a proxy for ms in this preview.
- **Preview bands** (value -> score):

| Range (ms) | Score | Grade |
| --- | --- | --- |
| <= 1 | +3 | A |
| <= 5 | +2 | B |
| <= 15 | +1 | C |
| <= 30 | 0 | AVG |
| <= 60 | -1 | D |
| <= 120 | -2 | E |
| > 120 | -3 | F |

### Milliseconds per Transaction for Batch

- **Formula**: `(batch_cpu_time_used * 1000) / batch_jobs_completed`
- **Meaning**: lower is better.
- **Preview bands** (value -> score):

| Range (ms) | Score | Grade |
| --- | --- | --- |
| <= 100 | +3 | A |
| <= 250 | +2 | B |
| <= 500 | +1 | C |
| <= 1000 | 0 | AVG |
| <= 2000 | -1 | D |
| <= 4000 | -2 | E |
| > 4000 | -3 | F |

### Throughput Efficiency Ratio

- **Formula**: `workload_processed / cpu_time_used`
- **Meaning**: higher is better (more work per CPU second).
- **Preview bands** (value -> score):

| Range | Score | Grade |
| --- | --- | --- |
| <= 20 | -3 | F |
| <= 40 | -2 | E |
| <= 60 | -1 | D |
| <= 80 | 0 | AVG |
| <= 120 | +1 | C |
| <= 160 | +2 | B |
| > 160 | +3 | A |

### I/O Efficiency Ratio

- **Formula**: `workload_processed / io_operations`
- **Meaning**: higher is better (more useful work per I/O).
- **Preview bands** (value -> score):

| Range | Score | Grade |
| --- | --- | --- |
| <= 0.20 | -3 | F |
| <= 0.40 | -2 | E |
| <= 0.55 | -1 | D |
| <= 0.70 | 0 | AVG |
| <= 0.85 | +1 | C |
| <= 0.95 | +2 | B |
| > 0.95 | +3 | A |

### Batch Efficiency Ratio

- **Formula**: `batch_jobs_completed / total_batch_window_minutes`
- **Meaning**: higher is better (more jobs per batch-window minute).
- **Preview bands** (value -> score):

| Range | Score | Grade |
| --- | --- | --- |
| <= 1 | -3 | F |
| <= 2 | -2 | E |
| <= 3 | -1 | D |
| <= 5 | 0 | AVG |
| <= 8 | +1 | C |
| <= 12 | +2 | B |
| > 12 | +3 | A |

### Cost Efficiency Ratio

- **Formula**: `workload_processed / cost`
- **Meaning**: higher is better (more work per cost unit).
- **Preview bands** (value -> score):

| Range | Score | Grade |
| --- | --- | --- |
| <= 50 | -3 | F |
| <= 150 | -2 | E |
| <= 300 | -1 | D |
| <= 500 | 0 | AVG |
| <= 900 | +1 | C |
| <= 1500 | +2 | B |
| > 1500 | +3 | A |

## Required input fields

| Field | Used by ratios |
| --- | --- |
| `cpu_time_used` | CPU Utilization, Throughput Efficiency |
| `total_cpu_capacity` | CPU Utilization |
| `online_cpu_time_used` | Online ms/Transaction |
| `total_transactions` | Online ms/Transaction |
| `batch_cpu_time_used` | Batch ms/Transaction |
| `batch_jobs_completed` | Batch ms/Transaction, Batch Efficiency |
| `total_batch_window_minutes` | Batch Efficiency |
| `io_operations` | I/O Efficiency |
| `workload_processed` | Throughput, I/O, Cost Efficiency |
| `cost` | Cost Efficiency |

Missing/zero values produce an `unavailable` ratio entry with a reason rather
than crashing.

## Overall score and grade

The overall score is the rounded average of all **available** ratio scores; the
overall grade is mapped from that average. Bands and grades are documented and
transparent — no hidden tuning.