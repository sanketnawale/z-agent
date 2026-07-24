import os
import sys

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)

from django.test import SimpleTestCase, TestCase

from agent.masking import mask_spool_text
from agent.prompts import build_spool_explanation_prompt

from .models import AuditLog
from .safety import is_action_allowed, mask_secret, mask_text


class SafetyModeTests(SimpleTestCase):
    def test_read_only_blocks_submit_jcl(self):
        self.assertFalse(is_action_allowed("SUBMIT_JCL", "READ_ONLY"))

    def test_execute_allows_submit_jcl(self):
        self.assertTrue(is_action_allowed("SUBMIT_JCL", "EXECUTE"))

    def test_approval_required_blocks_without_approval(self):
        self.assertFalse(is_action_allowed("SUBMIT_JCL", "APPROVAL_REQUIRED", approved=False))

    def test_approval_required_allows_with_approval(self):
        self.assertTrue(is_action_allowed("SUBMIT_JCL", "APPROVAL_REQUIRED", approved=True))

    def test_read_actions_allowed(self):
        self.assertTrue(is_action_allowed("VIEW_JOBS", "READ_ONLY"))
        self.assertTrue(is_action_allowed("VIEW_SPOOL", "READ_ONLY"))
        self.assertTrue(is_action_allowed("AI_EXPLAIN", "READ_ONLY"))

    def test_ai_explain_spool_allowed_in_read_only(self):
        self.assertTrue(is_action_allowed("AI_EXPLAIN_SPOOL", "READ_ONLY"))

    def test_mask_secret(self):
        self.assertEqual(mask_secret("abcd"), "****")
        self.assertEqual(mask_secret("abcdef"), "ab****ef")

    def test_mask_text_masks_sensitive_lines(self):
        text = "normal line\npassword=hello\nanother line"
        masked = mask_text(text)
        self.assertIn("normal line", masked)
        self.assertIn("[MASKED_SECRET_LINE]", masked)
        self.assertIn("another line", masked)


class MaskingUtilityTests(SimpleTestCase):
    """Mirror of agent.masking tests, runnable under the Django test runner."""

    def test_masks_dataset_and_password(self):
        masked = mask_spool_text(
            "Allocation failed for USER01.PAYROLL.PROD.INPUT password=abc123"
        )
        self.assertIn("<DATASET_NAME>", masked)
        self.assertIn("password=<REDACTED>", masked)
        self.assertNotIn("abc123", masked)
        self.assertNotIn("USER01.PAYROLL.PROD.INPUT", masked)

    def test_keeps_message_codes_visible(self):
        masked = mask_spool_text("IEFC621D IGYPS2113-E")
        self.assertIn("IEFC621D", masked)


class PromptBuilderDjangoTests(SimpleTestCase):
    def test_prompt_has_safety_rules(self):
        prompt = build_spool_explanation_prompt(
            "IEFC621D ALLOCATION FAILED", job_id="JOB12345"
        )
        self.assertIn("Do not recommend destructive actions", prompt)
        self.assertIn("Job ID: JOB12345", prompt)


_SPIECEXPLAIN_OK = {
    "status": "explained",
    "likely_cause": "Input dataset allocation failure",
    "evidence": "Spool contains a dataset allocation or not found message.",
    "suggested_next_step": "Verify the DD statement and confirm that the dataset exists.",
    "confidence": "medium",
    "ai_used": True,
    "model": "llama3.2:3b",
    "masked": True,
}

_SPIECEXPLAIN_ERR = {
    "status": "error",
    "message": "AI explanation is currently unavailable.",
    "ai_used": False,
}


def _set_session(request):
    request.session["zowe_profile"] = {
        "host": "demo.example.org",
        "port": "10443",
        "user": "TESTUSR",
        "password": "should-not-leak",
        "ru": "false",
    }
    request.session["ai_profile"] = {
        "provider": "server_ollama",
        "model": "llama3.2:3b",
        "api_key": "",
        "ollama_url": "http://127.0.0.1:11434/api/generate",
    }
    request.session["safety_mode"] = "READ_ONLY"


class ExplainSpoolEndpointTests(TestCase):
    """DB-backed tests for the /explain-spool/ Django proxy view + audit logging."""

    def _post(self, payload):
        from django.test import Client
        from importlib import import_module
        from django.conf import settings
        import json as _json

        client = Client()
        engine = import_module(settings.SESSION_ENGINE)
        session = engine.SessionStore()
        session["zowe_profile"] = {
            "host": "demo.example.org", "port": "10443", "user": "TESTUSR",
            "password": "should-not-leak", "ru": "false",
        }
        session["ai_profile"] = {
            "provider": "server_ollama", "model": "llama3.2:3b", "api_key": "",
            "ollama_url": "http://127.0.0.1:11434/api/generate",
        }
        session["safety_mode"] = "READ_ONLY"
        session.save()
        client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key

        return client.post(
            "/explain-spool/",
            data=_json.dumps(payload),
            content_type="application/json",
        )

    def test_success_path_creates_audit_log(self):
        import unittest.mock as mock

        with mock.patch("jobs.views.backend_post", return_value=dict(_SPIECEXPLAIN_OK)):
            response = self._post({"job_id": "JOB12345", "spool_text": "IEFC621D ALLOCATION FAILED"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "explained")
        self.assertEqual(body["job_id"], "JOB12345")
        self.assertTrue(body["ai_used"])
        self.assertTrue(body["masked"])
        self.assertEqual(body["confidence"], "medium")
        self.assertIsNotNone(body.get("audit_id"))
        self.assertRegex(body["audit_id"], r"^AUD-\d{6}$")

        audit = AuditLog.objects.filter(action="AI_EXPLAIN_SPOOL").order_by("-id").first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.status, "ALLOWED")
        self.assertEqual(audit.safety_mode, "READ_ONLY")
        self.assertEqual(audit.target, "JOB12345")

    def test_ollama_failure_path_returns_safe_error(self):
        import unittest.mock as mock

        with mock.patch("jobs.views.backend_post", return_value=dict(_SPIECEXPLAIN_ERR)):
            response = self._post({"job_id": "JOB99999", "spool_text": "anything"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "error")
        self.assertFalse(body["ai_used"])
        self.assertNotIn("exception", body)
        self.assertNotIn("traceback", body)

        audit = AuditLog.objects.filter(
            action="AI_EXPLAIN_SPOOL", target="JOB99999"
        ).order_by("-id").first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.status, "FAILED")

    def test_raw_secrets_are_not_stored_in_audit(self):
        secret = "password=supersecretvalue"
        import unittest.mock as mock

        with mock.patch("jobs.views.backend_post", return_value=dict(_SPIECEXPLAIN_OK)):
            self._post({"job_id": "JOBSECRET", "spool_text": secret})

        rows = AuditLog.objects.filter(action="AI_EXPLAIN_SPOOL")
        self.assertTrue(rows.exists())
        for row in rows:
            combined = f"{row.target or ''} {row.details or ''} {row.username or ''}"
            self.assertNotIn("supersecretvalue", combined)

    def test_backend_connection_error_returns_safe_error(self):
        import requests
        import unittest.mock as mock

        with mock.patch("jobs.views.backend_post",
                        side_effect=requests.exceptions.ConnectionError("no fastapi")):
            response = self._post({"job_id": "JOBCONN", "spool_text": "spool"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "error")
        self.assertFalse(body["ai_used"])


_JOB_SUMMARY_OK = {
    "job_id": "JOB12345", "job_name": "PAYROLL01", "status": "FAILED",
    "return_code": "RC=12", "result": "failure",
    "likely_cause": "Input dataset allocation failure",
    "evidence": "Spool contains a dataset allocation failure message.",
    "suggested_next_step": "Verify the DD statement and dataset name.",
    "confidence": "medium", "ai_used": True, "safe_to_continue": False,
}

_INCIDENT_OK = {
    "title": "IBM Z job PAYROLL01 failed with RC=12", "severity": "medium",
    "summary": "The job failed due to a likely input dataset allocation issue.",
    "evidence": "Spool contains a dataset allocation failure message.",
    "recommended_owner": "Payroll Team",
    "suggested_next_step": "Verify the DD statement and dataset availability.",
}

_NOTIFY_DRY_RUN_OK = {
    "status": "dry_run",
    "message": "Notification payload generated but not sent.",
    "payload": {"job_id": "JOB12345", "job_name": "PAYROLL01",
                "summary": "Job failed with RC=12", "source": "z-agent"},
}


def _devops_post(payload, url="/api/devops/job-summary"):
    from django.test import Client
    from importlib import import_module
    from django.conf import settings
    import json as _json

    client = Client()
    engine = import_module(settings.SESSION_ENGINE)
    session = engine.SessionStore()
    session["safety_mode"] = "EXECUTE"
    session.save()
    client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
    return client.post(url, data=_json.dumps(payload), content_type="application/json")


class DevOpsJobSummaryTests(TestCase):
    def test_success_path_creates_audit_log(self):
        import unittest.mock as mock
        with mock.patch("jobs.views.devops_backend_post", return_value=dict(_JOB_SUMMARY_OK)):
            response = _devops_post(
                {"job_id": "JOB12345", "job_name": "PAYROLL01",
                 "include_ai_explanation": True},
                url="/api/devops/job-summary",
            )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "FAILED")
        self.assertEqual(body["return_code"], "RC=12")
        self.assertFalse(body["safe_to_continue"])
        self.assertRegex(body["audit_id"], r"^AUD-\d{6}$")
        audit = AuditLog.objects.filter(action="DEVOPS_JOB_SUMMARY").order_by("-id").first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.status, "ALLOWED")
        self.assertEqual(audit.target, "JOB12345")

    def test_ai_unavailable_path_returns_basic_summary(self):
        import unittest.mock as mock
        basic = {"job_id": "JOB12345", "status": "FAILED", "return_code": "RC=12",
                 "result": "failure", "ai_used": False, "safe_to_continue": False}
        with mock.patch("jobs.views.devops_backend_post", return_value=basic):
            response = _devops_post({"job_id": "JOB12345"}, url="/api/devops/job-summary")
        body = response.json()
        self.assertFalse(body["ai_used"])
        self.assertFalse(body["safe_to_continue"])


class DevOpsIncidentSummaryTests(TestCase):
    def test_incident_summary_creates_audit(self):
        import unittest.mock as mock
        with mock.patch("jobs.views.devops_backend_post", return_value=dict(_INCIDENT_OK)):
            response = _devops_post(
                {"job_id": "JOB12345", "job_name": "PAYROLL01", "include_ai_explanation": False},
                url="/api/devops/incident-summary",
            )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("RC=12", body["title"])
        self.assertEqual(body["recommended_owner"], "Payroll Team")
        self.assertRegex(body["audit_id"], r"^AUD-\d{6}$")
        audit = AuditLog.objects.filter(action="DEVOPS_INCIDENT_SUMMARY").first()
        self.assertIsNotNone(audit)

    def test_incident_audit_does_not_store_raw_spool(self):
        import unittest.mock as mock
        secret = "password=topsecretvalue"
        with mock.patch("jobs.views.devops_backend_post", return_value=dict(_INCIDENT_OK)):
            _devops_post(
                {"job_id": "JOBSEC", "job_name": "SEC", "spool_text": secret,
                 "include_ai_explanation": False},
                url="/api/devops/incident-summary",
            )
        for row in AuditLog.objects.filter(action="DEVOPS_INCIDENT_SUMMARY"):
            combined = f"{row.target or ''} {row.details or ''}"
            self.assertNotIn("topsecretvalue", combined)


class DevOpsNotifyTests(TestCase):
    def test_dry_run_does_not_send_and_creates_audit(self):
        import unittest.mock as mock
        with mock.patch("jobs.views.devops_backend_post", return_value=dict(_NOTIFY_DRY_RUN_OK)) \
                as posted:
            response = _devops_post(
                {"webhook_url": "https://example.org/webhook", "job_id": "JOB12345",
                 "job_name": "PAYROLL01", "summary": "Job failed with RC=12",
                 "dry_run": True},
                url="/api/devops/notify",
            )
        posted.assert_called_once()
        sent_payload = posted.call_args.args[2]
        self.assertTrue(sent_payload["dry_run"])
        body = response.json()
        self.assertEqual(body["status"], "dry_run")
        self.assertNotIn("token", body["payload"])
        audit = AuditLog.objects.filter(action="DEVOPS_NOTIFY_DRY_RUN").first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.status, "ALLOWED")

    def test_dry_run_is_default_when_omitted(self):
        import unittest.mock as mock
        captured = {}
        def fake_post(*a, **k):
            captured["payload"] = a[2]
            return dict(_NOTIFY_DRY_RUN_OK)
        with mock.patch("jobs.views.devops_backend_post", side_effect=fake_post):
            response = _devops_post(
                {"webhook_url": "https://example.org/webhook", "job_id": "JOB1",
                 "summary": "fail"},
                url="/api/devops/notify",
            )
        self.assertTrue(captured["payload"]["dry_run"])
        self.assertEqual(response.json()["status"], "dry_run")

    def test_real_send_blocked_in_read_only(self):
        from django.test import Client
        from importlib import import_module
        from django.conf import settings
        import json as _json
        client = Client()
        engine = import_module(settings.SESSION_ENGINE)
        session = engine.SessionStore()
        session["safety_mode"] = "READ_ONLY"
        session.save()
        client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
        response = client.post(
            "/api/devops/notify",
            data=_json.dumps({"webhook_url": "https://example.org/wh",
                             "job_id": "JOB1", "dry_run": False}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)
        audit = AuditLog.objects.filter(action="DEVOPS_NOTIFY_SENT", status="BLOCKED").first()
        self.assertIsNotNone(audit)


# ---------------------------------------------------------------------------
# v0.7.0 Performance Insights tests
# ---------------------------------------------------------------------------

_PERF_OK = {
    "system_name": "demo-lpar", "period": "2026-07-demo",
    "overall_grade": "C", "overall_score": 1,
    "summary": "The system appears slightly above average based on the provided statistical ratios.",
    "ratios": [
        {"name": "CPU Utilization Ratio", "value": 0.5, "grade": "AVG", "score": 0,
         "interpretation": "CPU utilization is within the average range."},
        {"name": "Batch Efficiency Ratio", "value": 3.33, "grade": "C", "score": 1,
         "interpretation": "Batch processing efficiency is slightly above average."},
    ],
    "estimated_improvement_opportunity": "may save about 6% with optimization",
    "benchmark_mode": "local-scale-only",
    "ai_explanation": {"available": True,
                       "summary": "Advisory summary.",
                       "key_findings": ["batch above average"],
                       "possible_optimization_areas": ["review CPU"],
                       "safe_next_steps": ["monitor"],
                       "limitations": "preview thresholds only"},
    "disclaimer": "The v0.7.0 Performance Insights Preview ...",
}

_PERF_AI_UNAVAILABLE = {
    "system_name": "demo-lpar", "period": "2026-07-demo",
    "overall_grade": "C", "overall_score": 1, "ratios": [],
    "benchmark_mode": "local-scale-only",
    "ai_explanation": {"available": False,
                       "message": "AI explanation unavailable. Ratio calculations returned without AI explanation."},
}


def _perf_post(payload, safety_mode="EXECUTE"):
    from django.test import Client
    from importlib import import_module
    from django.conf import settings
    import json as _json

    client = Client()
    engine = import_module(settings.SESSION_ENGINE)
    session = engine.SessionStore()
    session["safety_mode"] = safety_mode
    session.save()
    client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
    return client.post("/api/performance/insights", data=_json.dumps(payload),
                       content_type="application/json")


class PerformanceInsightsEndpointTests(TestCase):
    def test_success_path_creates_audit_log(self):
        import unittest.mock as mock
        with mock.patch("jobs.views.devops_backend_post", return_value=dict(_PERF_OK)):
            response = _perf_post({
                "system_name": "demo-lpar", "period": "2026-07-demo",
                "metrics": {"cpu_time_used": 7200, "total_cpu_capacity": 14400,
                            "workload_processed": 500000, "cost": 1200},
                "include_ai_explanation": True,
            })
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["overall_grade"], "C")
        self.assertEqual(body["benchmark_mode"], "local-scale-only")
        self.assertTrue(body["ai_explanation"]["available"])
        self.assertRegex(body["audit_id"], r"^AUD-\d{6}$")
        audit = AuditLog.objects.filter(action="PERFORMANCE_INSIGHTS_ANALYSIS").order_by("-id").first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.status, "ALLOWED")
        self.assertEqual(audit.target, "demo-lpar")
        self.assertIn("raw values not stored", audit.details)
        self.assertIn("benchmark_mode=local-scale-only", audit.details)

    def test_ai_unavailable_path_returns_ratios(self):
        import unittest.mock as mock
        with mock.patch("jobs.views.devops_backend_post", return_value=dict(_PERF_AI_UNAVAILABLE)):
            response = _perf_post({
                "system_name": "demo-lpar", "period": "2026-07-demo",
                "metrics": {"cpu_time_used": 7200, "total_cpu_capacity": 14400},
                "include_ai_explanation": True,
            })
        body = response.json()
        self.assertFalse(body["ai_explanation"]["available"])
        self.assertEqual(body["overall_grade"], "C")

    def test_read_only_allows_performance_insights(self):
        import unittest.mock as mock
        with mock.patch("jobs.views.devops_backend_post", return_value=dict(_PERF_OK)):
            response = _perf_post(
                {"system_name": "demo-lpar", "period": "p",
                 "metrics": {"cpu_time_used": 1}, "include_ai_explanation": False},
                safety_mode="READ_ONLY",
            )
        self.assertEqual(response.status_code, 200)
        audit = AuditLog.objects.filter(action="PERFORMANCE_INSIGHTS_ANALYSIS").first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.safety_mode, "READ_ONLY")

    def test_raw_metrics_not_stored_in_audit(self):
        import unittest.mock as mock
        # Sensitive-looking metric value that must never appear in audit details.
        metrics = {"cpu_time_used": 987654321, "total_cpu_capacity": 10000,
                   "cost": 42, "workload_processed": 500000}
        with mock.patch("jobs.views.devops_backend_post", return_value=dict(_PERF_OK)):
            _perf_post({"system_name": "demo-lpar", "period": "p",
                        "metrics": metrics, "include_ai_explanation": False})
        for row in AuditLog.objects.filter(action="PERFORMANCE_INSIGHTS_ANALYSIS"):
            self.assertNotIn("987654321", row.details or "")
            self.assertNotIn("42", row.details or "")

    def test_invalid_metrics_return_safe_json_error(self):
        from django.test import Client
        from importlib import import_module
        from django.conf import settings
        client = Client()
        engine = import_module(settings.SESSION_ENGINE)
        session = engine.SessionStore()
        session["safety_mode"] = "EXECUTE"
        session.save()
        client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
        response = client.post("/api/performance/insights", data="not json",
                               content_type="application/json")
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body["status"], "error")
        # Acceptance criterion: invalid JSON returns JSON with an error key
        self.assertEqual(body["error"], "Invalid JSON")
        self.assertEqual(response["Content-Type"], "application/json")

    def test_backend_failure_returns_json_not_html(self):
        import requests
        import unittest.mock as mock
        with mock.patch("jobs.views.devops_backend_post",
                        side_effect=requests.exceptions.ConnectionError("no backend")):
            response = _perf_post({
                "system_name": "demo-lpar", "period": "p",
                "metrics": {"cpu_time_used": 7200, "total_cpu_capacity": 14400},
                "include_ai_explanation": False,
            })
        self.assertEqual(response.status_code, 502)
        body = response.json()
        self.assertEqual(body["status"], "error")
        self.assertIn("Failed to analyze performance metrics", body["error"])
        self.assertEqual(response["Content-Type"], "application/json")

    def test_unexpected_exception_returns_json_500(self):
        import unittest.mock as mock
        with mock.patch("jobs.views.devops_backend_post",
                        side_effect=RuntimeError("boom")):
            response = _perf_post({
                "system_name": "demo-lpar", "period": "p",
                "metrics": {}, "include_ai_explanation": False,
            })
        self.assertEqual(response.status_code, 500)
        body = response.json()
        self.assertEqual(body["status"], "error")
        self.assertEqual(response["Content-Type"], "application/json")

    def test_non_ai_analysis_returns_ratios(self):
        import unittest.mock as mock
        ok = dict(_PERF_OK)
        ok["ai_explanation"] = {"available": False,
                                "message": "AI explanation unavailable. Ratio calculations returned without AI explanation."}
        with mock.patch("jobs.views.devops_backend_post", return_value=dict(ok)):
            response = _perf_post({
                "system_name": "demo-lpar", "period": "2026-07-demo",
                "metrics": {"cpu_time_used": 7200, "total_cpu_capacity": 14400,
                            "workload_processed": 500000, "cost": 1200},
                "include_ai_explanation": False,
            })
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertFalse(body["ai_explanation"]["available"])
        self.assertTrue(len(body["ratios"]) >= 1)
        self.assertEqual(body["benchmark_mode"], "local-scale-only")
