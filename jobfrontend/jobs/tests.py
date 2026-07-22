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
