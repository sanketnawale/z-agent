"""Tests for the Performance Insights preview module (agent.performance_insights).

No IBM Z, no SMF/RMF, no Ollama, no benchmark dataset required.
"""

import unittest

from agent.performance_insights import (
    BENCHMARK_MODE_LOCAL,
    DISCLAIMER,
    build_performance_insights_report,
    calculate_batch_efficiency_ratio,
    calculate_batch_ms_per_transaction,
    calculate_cost_efficiency_ratio,
    calculate_cpu_utilization_ratio,
    calculate_io_efficiency_ratio,
    calculate_online_ms_per_transaction,
    calculate_throughput_efficiency_ratio,
    grade_standard_deviation_score,
    metrics_summary_for_audit,
    ratio_names,
)


def _sample_metrics():
    return {
        "cpu_time_used": 7200,
        "total_cpu_capacity": 14400,
        "online_cpu_time_used": 2500,
        "total_transactions": 100000,
        "batch_cpu_time_used": 4700,
        "batch_jobs_completed": 1200,
        "total_batch_window_minutes": 360,
        "io_operations": 850000,
        "workload_processed": 500000,
        "cost": 1200,
    }


class GradeMappingTests(unittest.TestCase):
    def test_scale_mapping(self):
        self.assertEqual(grade_standard_deviation_score(-3), "F")
        self.assertEqual(grade_standard_deviation_score(-2), "E")
        self.assertEqual(grade_standard_deviation_score(-1), "D")
        self.assertEqual(grade_standard_deviation_score(0), "AVG")
        self.assertEqual(grade_standard_deviation_score(1), "C")
        self.assertEqual(grade_standard_deviation_score(2), "B")
        self.assertEqual(grade_standard_deviation_score(3), "A")

    def test_clamps_extremes(self):
        self.assertEqual(grade_standard_deviation_score(-5), "F")
        self.assertEqual(grade_standard_deviation_score(5), "A")

    def test_invalid_returns_avg(self):
        self.assertEqual(grade_standard_deviation_score(None), "AVG")
        self.assertEqual(grade_standard_deviation_score("abc"), "AVG")
        self.assertEqual(grade_standard_deviation_score(1.4), "C")  # round


class RatioCalculationTests(unittest.TestCase):
    def test_cpu_utilization_ratio(self):
        self.assertAlmostEqual(calculate_cpu_utilization_ratio(_sample_metrics()), 0.5)

    def test_online_ms_per_transaction(self):
        self.assertAlmostEqual(
            calculate_online_ms_per_transaction(_sample_metrics()), 25.0
        )

    def test_batch_ms_per_transaction(self):
        self.assertAlmostEqual(
            calculate_batch_ms_per_transaction(_sample_metrics()),
            4700.0 * 1000 / 1200,
            places=2,
        )

    def test_throughput_efficiency_ratio(self):
        self.assertAlmostEqual(
            calculate_throughput_efficiency_ratio(_sample_metrics()),
            500000 / 7200,
            places=2,
        )

    def test_io_efficiency_ratio(self):
        self.assertAlmostEqual(
            calculate_io_efficiency_ratio(_sample_metrics()),
            500000 / 850000,
            places=4,
        )

    def test_batch_efficiency_ratio(self):
        self.assertAlmostEqual(
            calculate_batch_efficiency_ratio(_sample_metrics()),
            1200 / 360,
            places=4,
        )

    def test_cost_efficiency_ratio(self):
        self.assertAlmostEqual(
            calculate_cost_efficiency_ratio(_sample_metrics()),
            500000 / 1200,
            places=2,
        )


class SafeDivisionTests(unittest.TestCase):
    def test_zero_denominator_returns_none(self):
        m = {"cpu_time_used": 100, "total_cpu_capacity": 0}
        self.assertIsNone(calculate_cpu_utilization_ratio(m))

    def test_missing_values_return_none(self):
        self.assertIsNone(calculate_cpu_utilization_ratio({}))
        self.assertIsNone(calculate_online_ms_per_transaction({}))
        self.assertIsNone(calculate_batch_ms_per_transaction({}))
        self.assertIsNone(calculate_throughput_efficiency_ratio({}))
        self.assertIsNone(calculate_io_efficiency_ratio({}))
        self.assertIsNone(calculate_batch_efficiency_ratio({}))
        self.assertIsNone(calculate_cost_efficiency_ratio({}))

    def test_non_numeric_returns_none(self):
        m = {"cpu_time_used": "abc", "total_cpu_capacity": 10}
        self.assertIsNone(calculate_cpu_utilization_ratio(m))


class ReportBuilderTests(unittest.TestCase):
    def test_report_has_required_fields(self):
        report = build_performance_insights_report("demo-lpar", "2026-07-demo", _sample_metrics())
        for field in ("system_name", "period", "overall_grade", "overall_score",
                      "summary", "ratios", "estimated_improvement_opportunity",
                      "benchmark_mode", "disclaimer"):
            self.assertIn(field, report)
        self.assertEqual(report["system_name"], "demo-lpar")
        self.assertEqual(report["benchmark_mode"], BENCHMARK_MODE_LOCAL)
        self.assertIn(DISCLAIMER[:30], report["disclaimer"])

    def test_ratios_list_has_seven_entries(self):
        report = build_performance_insights_report("s", "p", _sample_metrics())
        self.assertEqual(len(report["ratios"]), 7)
        for entry in report["ratios"]:
            for key in ("name", "value", "grade", "score", "interpretation"):
                self.assertIn(key, entry)

    def test_missing_metrics_do_not_crash_and_grade_avg(self):
        report = build_performance_insights_report("s", "p", {})
        self.assertEqual(report["overall_grade"], "AVG")
        self.assertEqual(report["overall_score"], 0)
        for entry in report["ratios"]:
            self.assertIsNone(entry["value"])
            self.assertEqual(entry["grade"], "AVG")

    def test_local_scale_only_benchmark_mode(self):
        report = build_performance_insights_report("s", "p", _sample_metrics())
        self.assertEqual(report["benchmark_mode"], "local-scale-only")

    def test_non_dict_metrics_does_not_crash(self):
        report = build_performance_insights_report("s", "p", None)
        self.assertEqual(report["overall_grade"], "AVG")

    def test_ratio_names_and_audit_metadata(self):
        report = build_performance_insights_report("s", "p", _sample_metrics())
        names = ratio_names(report)
        self.assertEqual(len(names), 7)
        self.assertIn("CPU Utilization Ratio", names)
        meta = metrics_summary_for_audit(_sample_metrics())
        self.assertIn("metric_keys=", meta)
        self.assertIn("raw values not stored", meta)
        self.assertNotIn("7200", meta)


class AIExplanationParsingTests(unittest.TestCase):
    def test_ai_unavailable_safe_error_shape(self):
        from agent.ollama_service import _PERFORMANCE_SAFE_ERROR
        self.assertFalse(_PERFORMANCE_SAFE_ERROR["available"])
        self.assertIn("Ratio calculations returned", _PERFORMANCE_SAFE_ERROR["message"])

    def test_ai_timeout_error_shape(self):
        from agent.ollama_service import _PERFORMANCE_AI_TIMEOUT_ERROR
        self.assertFalse(_PERFORMANCE_AI_TIMEOUT_ERROR["available"])
        self.assertIn("timed out", _PERFORMANCE_AI_TIMEOUT_ERROR["message"])
        self.assertIn("Ratio calculations returned", _PERFORMANCE_AI_TIMEOUT_ERROR["message"])

    def test_ai_timeout_returns_ratios_without_ai(self):
        import requests
        import unittest.mock as mock
        from agent.ollama_service import explain_performance_insights_with_ollama

        with mock.patch("agent.ollama_service.requests.post",
                        side_effect=requests.exceptions.ReadTimeout("slow ollama")):
            result = explain_performance_insights_with_ollama(
                {"overall_grade": "C", "ratios": []},
                ai_config={"ollama_url": "http://127.0.0.1:11434"},
            )
        self.assertFalse(result["available"])
        self.assertIn("timed out", result["message"])
        self.assertNotIn("traceback", result)

    def test_ai_parses_structured_json(self):
        import unittest.mock as mock
        from agent.ollama_service import explain_performance_insights_with_ollama

        model_text = (
            '{"summary": "System slightly above average.", '
            '"key_findings": ["batch efficiency above average"], '
            '"possible_optimization_areas": ["review CPU utilization"], '
            '"safe_next_steps": ["monitor batch window"], '
            '"limitations": "preview thresholds only"}'
        )
        fake = mock.Mock()
        fake.raise_for_status.return_value = None
        fake.json.return_value = {"response": model_text}
        with mock.patch("agent.ollama_service.requests.post", return_value=fake):
            result = explain_performance_insights_with_ollama(
                {"overall_grade": "C", "ratios": []},
                ai_config={"ollama_url": "http://127.0.0.1:11434", "model": "llama3.2:3b"},
            )
        self.assertTrue(result["available"])
        self.assertEqual(result["summary"], "System slightly above average.")
        self.assertEqual(result["safe_next_steps"], ["monitor batch window"])
        self.assertEqual(result["limitations"], "preview thresholds only")

    def test_ai_connection_failure_returns_safe_error(self):
        import requests
        import unittest.mock as mock
        from agent.ollama_service import explain_performance_insights_with_ollama

        with mock.patch("agent.ollama_service.requests.post",
                        side_effect=requests.exceptions.ConnectionError("x")):
            result = explain_performance_insights_with_ollama(
                {"overall_grade": "C"}, ai_config={"ollama_url": "http://127.0.0.1:11434"}
            )
        self.assertFalse(result["available"])
        self.assertNotIn("traceback", result)


if __name__ == "__main__":
    unittest.main()