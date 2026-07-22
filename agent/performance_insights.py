"""
Performance Insights preview for z-agent (v0.7.0 Performance Insights Preview).

This module calculates mainframe efficiency ratios from *provided statistical*
metrics and assigns a grade based on a standard-deviation ratio scale concept.
It does NOT perform real benchmark comparison and does NOT require SMF/RMF
access in this preview.

The v0.7 preview uses local/demo thresholds. Real standard deviation
benchmarking requires an authorized benchmark dataset.

Safety/data-handling principles:

- collect statistical data only
- no programs installed
- use IBM utilities (future)
- do not collect source code, credentials, or sensitive business data
- raw metrics are never stored in audit logs (metadata only)

All calculations use safe division and never crash on zero/missing input --
insufficient input yields ``"unavailable"`` with a reason.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Scale / grade mapping (Ralph's standard deviation ratio scale concept)
# ---------------------------------------------------------------------------
#
# score <= -3 -> F (-3)
# score == -2 -> E (-2)
# score == -1 -> D (-1)
# score ==  0 -> AVG (average)
# score ==  1 -> C (+1)
# score ==  2 -> B (+2)
# score >=  3 -> A (+3)
#
# The v0.7 preview uses local/demo thresholds. Real standard deviation
# benchmarking requires an authorized benchmark dataset.

GRADE_BY_SCORE: Dict[int, str] = {
    -3: "F",
    -2: "E",
    -1: "D",
    0: "AVG",
    1: "C",
    2: "B",
    3: "A",
}

SCORE_BY_GRADE: Dict[str, int] = {v: k for k, v in GRADE_BY_SCORE.items()}

# Estimated improvement opportunity (advisory only) by grade.
# These mirror the document's description: B ~3%, C ~6%, D ~9%, E ~12%,
# F = severe underperformance, A = about perfect, AVG = average.
IMPROVEMENT_HINT: Dict[str, str] = {
    "A": "about perfect - minimal optimization opportunity indicated",
    "B": "may save about 3% with optimization",
    "C": "may save about 6% with optimization",
    "D": "may save about 9% with optimization",
    "E": "may save about 12% with optimization",
    "F": "severe underperformance - review recommended",
    "AVG": "review recommended",
}

BENCHMARK_MODE_LOCAL = "local-scale-only"

DISCLAIMER = (
    "The v0.7.0 Performance Insights Preview calculates ratios from provided "
    "statistical data and uses local/demo thresholds. It does not claim to "
    "compare against an external benchmark population unless an authorized "
    "benchmark dataset is configured in a future version."
)


def grade_standard_deviation_score(score: Any) -> str:
    """Map a numeric score to a grade (F..A / AVG).

    Unknown/None/non-numeric returns ``"AVG"`` (neutral) so the preview never
    crashes on bad input.
    """
    try:
        s = int(round(float(score)))
    except (TypeError, ValueError):
        return "AVG"
    if s <= -3:
        return "F"
    if s >= 3:
        return "A"
    return GRADE_BY_SCORE.get(s, "AVG")


# ---------------------------------------------------------------------------
# Safe helpers
# ---------------------------------------------------------------------------

def _num(metrics: Dict[str, Any], key: str) -> Optional[float]:
    value = metrics.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_div(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    """Division that returns None on missing/zero denominator instead of crashing."""
    if numerator is None or denominator is None:
        return None
    if denominator == 0:
        return None
    return numerator / denominator


def _ratio_entry(
    name: str,
    value: Optional[float],
    interpretation: str,
    reason: str = "",
) -> Dict[str, Any]:
    if value is None:
        return {
            "name": name,
            "value": None,
            "grade": "AVG",
            "score": 0,
            "interpretation": reason or f"{name} unavailable: insufficient input data.",
        }
    score = _local_score_for_ratio(name, value)
    grade = grade_standard_deviation_score(score)
    return {
        "name": name,
        "value": round(value, 4),
        "grade": grade,
        "score": score,
        "interpretation": interpretation,
    }


# ---------------------------------------------------------------------------
# Local/demo scoring (preview thresholds)
# ---------------------------------------------------------------------------
#
# The v0.7 preview does NOT have an authorized benchmark dataset. Each ratio
# uses simple, deterministic, documented placeholder bands to map a numeric
# ratio to a -3..+3 score. These are "preview local thresholds" and are NOT
# presented as real industry benchmarks.
#
# Bands are intentionally transparent intervals keyed by ratio name.

def _band_score(value: float, bands: List[Tuple[float, int]]) -> int:
    """Pick the score for the first band whose upper bound >= value.

    Each band is (upper_bound, score). Values above the last band get the last
    score; values below the first get the first score.
    """
    for upper, score in bands:
        if value <= upper:
            return score
    return bands[-1][1]


# CPU utilization: ~0.50 average. Too low = underutilization, too high = risk.
# Mid band is best (AVG/slightly above). Preview bands are symmetric-ish.
_CPU_UTIL_BANDS = [
    (0.20, -3),  # F very low utilization
    (0.35, -2),  # E
    (0.45, -1),  # D
    (0.55, 0),   # AVG
    (0.70, 1),   # C
    (0.80, 2),   # B
    (float("inf"), 3),  # A
]

# ms/transaction (online): lower is better. Preview bands are magnitude-based.
_ONLINE_MS_BANDS = [
    (1.0, 3),   # A excellent
    (5.0, 2),   # B
    (15.0, 1),  # C
    (30.0, 0),  # AVG
    (60.0, -1), # D
    (120.0, -2),# E
    (float("inf"), -3),  # F
]

# ms/transaction (batch): lower is better.
_BATCH_MS_BANDS = [
    (100.0, 3),
    (250.0, 2),
    (500.0, 1),
    (1000.0, 0),
    (2000.0, -1),
    (4000.0, -2),
    (float("inf"), -3),
]

# Throughput efficiency (work per CPU second): higher is better.
_THROUGHPUT_BANDS = [
    (20.0, -3),
    (40.0, -2),
    (60.0, -1),
    (80.0, 0),
    (120.0, 1),
    (160.0, 2),
    (float("inf"), 3),
]

# I/O efficiency (work per I/O): higher is better.
_IO_EFF_BANDS = [
    (0.20, -3),
    (0.40, -2),
    (0.55, -1),
    (0.70, 0),
    (0.85, 1),
    (0.95, 2),
    (float("inf"), 3),
]

# Batch efficiency (jobs per batch-window-minute): higher is better.
_BATCH_EFF_BANDS = [
    (1.0, -3),
    (2.0, -2),
    (3.0, -1),
    (5.0, 0),
    (8.0, 1),
    (12.0, 2),
    (float("inf"), 3),
]

# Cost efficiency (work per cost unit): higher is better.
_COST_EFF_BANDS = [
    (50.0, -3),
    (150.0, -2),
    (300.0, -1),
    (500.0, 0),
    (900.0, 1),
    (1500.0, 2),
    (float("inf"), 3),
]

_RATIO_BANDS = {
    "CPU Utilization Ratio": _CPU_UTIL_BANDS,
    "Milliseconds per Transaction Online": _ONLINE_MS_BANDS,
    "Milliseconds per Transaction for Batch": _BATCH_MS_BANDS,
    "Throughput Efficiency Ratio": _THROUGHPUT_BANDS,
    "I/O Efficiency Ratio": _IO_EFF_BANDS,
    "Batch Efficiency Ratio": _BATCH_EFF_BANDS,
    "Cost Efficiency Ratio": _COST_EFF_BANDS,
}


def _local_score_for_ratio(name: str, value: float) -> int:
    bands = _RATIO_BANDS.get(name)
    if not bands:
        return 0
    return _band_score(value, bands)


# ---------------------------------------------------------------------------
# Ratio calculations
# ---------------------------------------------------------------------------

def calculate_cpu_utilization_ratio(metrics: Dict[str, Any]) -> Optional[float]:
    """CPU Utilization Ratio = cpu_time_used / total_cpu_capacity.

    ~0.50 is average; extremely low or extremely high are outliers.
    """
    used = _num(metrics, "cpu_time_used")
    capacity = _num(metrics, "total_cpu_capacity")
    return _safe_div(used, capacity)


def calculate_online_ms_per_transaction(metrics: Dict[str, Any]) -> Optional[float]:
    """Online ms per transaction = (online_cpu_time_used*1000) / total_transactions.

    Lower is better. Uses cpu time as a proxy for ms in this preview.
    """
    online = _num(metrics, "online_cpu_time_used")
    tx = _num(metrics, "total_transactions")
    product = (online * 1000.0) if online is not None else None
    return _safe_div(product, tx)


def calculate_batch_ms_per_transaction(metrics: Dict[str, Any]) -> Optional[float]:
    """Batch ms per transaction = (batch_cpu_time_used*1000) / batch_jobs_completed.

    Lower is better. Uses cpu time as a proxy for ms in this preview.
    """
    batch = _num(metrics, "batch_cpu_time_used")
    jobs = _num(metrics, "batch_jobs_completed")
    product = (batch * 1000.0) if batch is not None else None
    return _safe_div(product, jobs)


def calculate_throughput_efficiency_ratio(metrics: Dict[str, Any]) -> Optional[float]:
    """Throughput efficiency = workload_processed / cpu_time_used.

    Higher is better (more work per CPU second).
    """
    work = _num(metrics, "workload_processed")
    used = _num(metrics, "cpu_time_used")
    return _safe_div(work, used)


def calculate_io_efficiency_ratio(metrics: Dict[str, Any]) -> Optional[float]:
    """I/O efficiency = workload_processed / io_operations.

    Higher is better (more useful work per I/O).
    """
    work = _num(metrics, "workload_processed")
    io = _num(metrics, "io_operations")
    return _safe_div(work, io)


def calculate_batch_efficiency_ratio(metrics: Dict[str, Any]) -> Optional[float]:
    """Batch efficiency = batch_jobs_completed / total_batch_window_minutes.

    Higher is better (more jobs per window minute).
    """
    jobs = _num(metrics, "batch_jobs_completed")
    window = _num(metrics, "total_batch_window_minutes")
    return _safe_div(jobs, window)


def calculate_cost_efficiency_ratio(metrics: Dict[str, Any]) -> Optional[float]:
    """Cost efficiency = workload_processed / cost.

    Higher is better (more work per cost unit).
    """
    work = _num(metrics, "workload_processed")
    cost = _num(metrics, "cost")
    return _safe_div(work, cost)


# ---------------------------------------------------------------------------
# Report builder
# ---------------------------------------------------------------------------

def _interpretation_for(name: str, grade: str) -> str:
    lower = {
        "CPU Utilization Ratio": "CPU utilization",
        "Milliseconds per Transaction Online": "Online ms per transaction",
        "Milliseconds per Transaction for Batch": "Batch ms per transaction",
        "Throughput Efficiency Ratio": "Throughput efficiency",
        "I/O Efficiency Ratio": "I/O efficiency",
        "Batch Efficiency Ratio": "Batch processing efficiency",
        "Cost Efficiency Ratio": "Cost efficiency",
    }.get(name, name)
    band = {
        "A": "is excellent",
        "B": "is above average",
        "C": "is slightly above average",
        "AVG": "is within the average range",
        "D": "is slightly below average",
        "E": "is below average",
        "F": "indicates severe underperformance",
    }.get(grade, "is within the average range")
    return f"{lower} {band}."


def _ratio_entries(metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []

    cpu = calculate_cpu_utilization_ratio(metrics)
    entries.append(_ratio_entry(
        "CPU Utilization Ratio", cpu,
        _interpretation_for("CPU Utilization Ratio", grade_standard_deviation_score(
            _local_score_for_ratio("CPU Utilization Ratio", cpu) if cpu is not None else 0
        )),
    ))

    online = calculate_online_ms_per_transaction(metrics)
    entries.append(_ratio_entry(
        "Milliseconds per Transaction Online", online,
        _interpretation_for("Milliseconds per Transaction Online",
                            grade_standard_deviation_score(
                                _local_score_for_ratio("Milliseconds per Transaction Online", online)
                                if online is not None else 0)),
    ))

    batch_ms = calculate_batch_ms_per_transaction(metrics)
    entries.append(_ratio_entry(
        "Milliseconds per Transaction for Batch", batch_ms,
        _interpretation_for("Milliseconds per Transaction for Batch",
                            grade_standard_deviation_score(
                                _local_score_for_ratio("Milliseconds per Transaction for Batch", batch_ms)
                                if batch_ms is not None else 0)),
    ))

    throughput = calculate_throughput_efficiency_ratio(metrics)
    entries.append(_ratio_entry(
        "Throughput Efficiency Ratio", throughput,
        _interpretation_for("Throughput Efficiency Ratio",
                            grade_standard_deviation_score(
                                _local_score_for_ratio("Throughput Efficiency Ratio", throughput)
                                if throughput is not None else 0)),
    ))

    io = calculate_io_efficiency_ratio(metrics)
    entries.append(_ratio_entry(
        "I/O Efficiency Ratio", io,
        _interpretation_for("I/O Efficiency Ratio",
                            grade_standard_deviation_score(
                                _local_score_for_ratio("I/O Efficiency Ratio", io)
                                if io is not None else 0)),
    ))

    batch_eff = calculate_batch_efficiency_ratio(metrics)
    entries.append(_ratio_entry(
        "Batch Efficiency Ratio", batch_eff,
        _interpretation_for("Batch Efficiency Ratio",
                            grade_standard_deviation_score(
                                _local_score_for_ratio("Batch Efficiency Ratio", batch_eff)
                                if batch_eff is not None else 0)),
    ))

    cost = calculate_cost_efficiency_ratio(metrics)
    entries.append(_ratio_entry(
        "Cost Efficiency Ratio", cost,
        _interpretation_for("Cost Efficiency Ratio",
                            grade_standard_deviation_score(
                                _local_score_for_ratio("Cost Efficiency Ratio", cost)
                                if cost is not None else 0)),
    ))

    return entries


def _overall_score(entries: List[Dict[str, Any]]) -> int:
    valid_scores = [int(e["score"]) for e in entries if e.get("value") is not None]
    if not valid_scores:
        return 0
    avg = sum(valid_scores) / len(valid_scores)
    try:
        return int(round(avg))
    except (TypeError, ValueError):
        return 0


def _overall_summary(grade: str) -> str:
    base = {
        "A": "The system appears excellent based on the provided statistical ratios.",
        "B": "The system appears above average based on the provided statistical ratios.",
        "C": "The system appears slightly above average based on the provided statistical ratios.",
        "AVG": "The system appears average based on the provided statistical ratios.",
        "D": "The system appears slightly below average based on the provided statistical ratios.",
        "E": "The system appears below average based on the provided statistical ratios.",
        "F": "The system appears to have severe underperformance based on the provided ratios.",
    }.get(grade, "The system appears average based on the provided statistical ratios.")
    return base


def build_performance_insights_report(
    system_name: str,
    period: str,
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    """Build a structured performance insights report.

    Never raises. Always returns ``benchmark_mode`` = ``local-scale-only`` and a
    disclaimer. Insufficient input produces ``unavailable`` ratio entries
    rather than crashing.
    """
    if not isinstance(metrics, dict):
        metrics = {}

    entries = _ratio_entries(metrics)
    overall_score = _overall_score(entries)
    overall_grade = grade_standard_deviation_score(overall_score)

    return {
        "system_name": str(system_name or "unknown"),
        "period": str(period or "unknown"),
        "overall_grade": overall_grade,
        "overall_score": overall_score,
        "summary": _overall_summary(overall_grade),
        "ratios": entries,
        "estimated_improvement_opportunity": IMPROVEMENT_HINT.get(
            overall_grade, "review recommended"
        ),
        "benchmark_mode": BENCHMARK_MODE_LOCAL,
        "disclaimer": DISCLAIMER,
    }


def ratio_names(report: Dict[str, Any]) -> List[str]:
    """Helper for audit metadata: list the ratio names that were calculated."""
    return [str(e.get("name", "")) for e in report.get("ratios", []) if e.get("name")]


def metrics_summary_for_audit(metrics: Dict[str, Any]) -> str:
    """Produce a safe, non-secret metadata string about the metrics input.

    Never includes raw values; reports only which keys were present.
    """
    if not isinstance(metrics, dict):
        return "no metrics"
    keys = sorted(str(k) for k in metrics.keys())
    return f"metric_keys={','.join(keys)}; raw values not stored"