"""Tests for the DevOps integration helpers (agent.devops).

No IBM Z, no Ollama, no real webhooks required.
"""

import os
import tempfile
import unittest

from agent.devops import (
    UNKNOWN_OWNER,
    build_incident_summary,
    build_job_summary,
    build_notify_payload,
    load_ownership_rules,
    match_owner,
    notify,
)


def _diagnosis(failed=True, rc="12"):
    return {
        "jobname": "PAYROLL01",
        "final_rc": rc,
        "headline": "JCL validation failed",
        "root_cause": "JES rejected the submitted JCL.",
        "fix": "Inspect JESJCL for the IEFC message and correct the JCL.",
        "severity": "error" if failed else "success",
        "evidence": ["IEFC621D ALLOCATION FAILED", "IEFC660E"],
    }


def _ai_ok():
    return {
        "status": "explained",
        "likely_cause": "Input dataset allocation failure",
        "evidence": "Spool contains a dataset allocation failure message.",
        "suggested_next_step": "Verify the DD statement and dataset name.",
        "confidence": "medium",
        "ai_used": True,
        "model": "llama3.2:3b",
    }


def _ownership_yaml():
    return (
        'ownership_rules:\n'
        '  - job_pattern: "PAY*"\n'
        '    team: "Payroll Team"\n'
        '    notify:\n'
        '      email: "payroll-ops@example.org"\n'
        '      webhook: "https://example.org/webhook/payroll"\n'
        '  - job_pattern: "BILL*"\n'
        '    team: "Billing Team"\n'
        '    notify:\n'
        '      email: "billing-ops@example.org"\n'
        '  - job_pattern: "DEV*"\n'
        '    team: "Development Team"\n'
        '    notify:\n'
        '      email: "dev-mainframe@example.org"\n'
    )


class OwnershipRulesTests(unittest.TestCase):
    def test_load_and_match_payroll(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write(_ownership_yaml())
            path = f.name
        try:
            rules = load_ownership_rules(path)
            self.assertEqual(len(rules), 3)
            owner = match_owner("PAYROLL01", rules)
            self.assertEqual(owner["team"], "Payroll Team")
            self.assertEqual(owner["notify"]["email"], "payroll-ops@example.org")
        finally:
            os.unlink(path)

    def test_match_billing(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
            f.write(_ownership_yaml())
            path = f.name
        try:
            rules = load_ownership_rules(path)
            owner = match_owner("BILLING02", rules)
            self.assertEqual(owner["team"], "Billing Team")
        finally:
            os.unlink(path)

    def test_unknown_owner_fallback(self):
        rules = load_ownership_rules("")  # no file
        owner = match_owner("UNKNOWNJOB", rules)
        self.assertEqual(owner["team"], UNKNOWN_OWNER)
        self.assertEqual(owner["notify"], {})

    def test_missing_file_returns_empty(self):
        rules = load_ownership_rules("/nonexistent/path/to/rules.yaml")
        self.assertEqual(rules, [])

    def test_match_owner_case_insensitive(self):
        rules = [{"job_pattern": "pay*", "team": "Payroll", "notify": {}}]
        self.assertEqual(match_owner("payroll99", rules)["team"], "Payroll")


class JobSummaryTests(unittest.TestCase):
    def test_failed_job_summary_with_ai(self):
        summary = build_job_summary("JOB12345", "PAYROLL01", _diagnosis(), _ai_ok())
        self.assertEqual(summary["job_id"], "JOB12345")
        self.assertEqual(summary["job_name"], "PAYROLL01")
        self.assertEqual(summary["status"], "FAILED")
        self.assertEqual(summary["return_code"], "RC=12")
        self.assertEqual(summary["result"], "failure")
        self.assertEqual(summary["likely_cause"], "Input dataset allocation failure")
        self.assertEqual(summary["confidence"], "medium")
        self.assertTrue(summary["ai_used"])
        self.assertFalse(summary["safe_to_continue"])

    def test_failed_job_summary_without_ai(self):
        summary = build_job_summary("JOB12345", "PAYROLL01", _diagnosis(), None)
        self.assertEqual(summary["status"], "FAILED")
        self.assertFalse(summary["ai_used"])
        self.assertFalse(summary["safe_to_continue"])
        self.assertIn("JCL validation failed", summary["likely_cause"])
        self.assertEqual(summary["return_code"], "RC=12")

    def test_ai_unavailable_keeps_rule_based_fields(self):
        ai_err = {"status": "error", "ai_used": False, "message": "unavailable"}
        summary = build_job_summary("JOB1", "JOB1", _diagnosis(), ai_err)
        self.assertFalse(summary["ai_used"])
        self.assertEqual(summary["confidence"], "low")
        self.assertFalse(summary["safe_to_continue"])

    def test_success_job_summary_safe_to_continue(self):
        summary = build_job_summary("JOB00001", "PAYROLL01", _diagnosis(failed=False, rc="0000"), None)
        self.assertEqual(summary["status"], "SUCCESS")
        self.assertEqual(summary["return_code"], "RC=0000")
        self.assertEqual(summary["result"], "success")
        self.assertTrue(summary["safe_to_continue"])

    def test_return_code_formatting(self):
        diag = _diagnosis(rc="8")
        self.assertEqual(build_job_summary("J", "N", diag, None)["return_code"], "RC=8")


class IncidentSummaryTests(unittest.TestCase):
    def test_incident_summary_with_ai_and_ownership(self):
        ownership = {"team": "Payroll Team", "notify": {"email": "payroll-ops@example.org"}}
        inc = build_incident_summary("JOB12345", "PAYROLL01", _diagnosis(), _ai_ok(), ownership)
        self.assertIn("PAYROLL01", inc["title"])
        self.assertIn("RC=12", inc["title"])
        self.assertEqual(inc["severity"], "medium")
        self.assertEqual(inc["recommended_owner"], "Payroll Team")
        self.assertEqual(inc["summary"], "Input dataset allocation failure")

    def test_incident_summary_unknown_owner(self):
        inc = build_incident_summary("JOB1", "MYSTERY", _diagnosis(), None, None)
        self.assertEqual(inc["recommended_owner"], UNKNOWN_OWNER)

    def test_incident_high_severity_for_abend(self):
        diag = _diagnosis(failed=True, rc="S0C7")
        diag["headline"] = "Job ended with ABEND"
        inc = build_incident_summary("JOB1", "J1", diag, None,
                                     {"team": "T", "notify": {}})
        self.assertEqual(inc["severity"], "high")

    def test_incident_success_is_low(self):
        inc = build_incident_summary("JOB1", "J1", _diagnosis(failed=False, rc="0000"), None,
                                     {"team": "T", "notify": {}})
        self.assertEqual(inc["severity"], "low")
        self.assertIn("completed successfully", inc["title"])


class NotifyTests(unittest.TestCase):
    def test_dry_run_does_not_send(self):
        with unittest.mock.patch("agent.devops.send_webhook_payload") as send_fn:
            result = notify(
                "https://example.org/webhook",
                "JOB12345", "PAYROLL01", "Job failed with RC=12",
                dry_run=True,
            )
        send_fn.assert_not_called()
        self.assertEqual(result["status"], "dry_run")
        self.assertEqual(result["payload"]["job_id"], "JOB12345")
        self.assertEqual(result["payload"]["job_name"], "PAYROLL01")
        self.assertEqual(result["payload"]["summary"], "Job failed with RC=12")
        self.assertNotIn("token", result["payload"])

    def test_build_payload_excludes_secrets(self):
        payload = build_notify_payload(
            "https://example.org/webhook", "JOB1", "JOB1", "summary",
            extra={"token": "secret", "job_id": "JOB1", "password": "x"},
        )
        self.assertNotIn("token", payload)
        self.assertNotIn("password", payload)
        self.assertEqual(payload["job_id"], "JOB1")

    def test_dry_run_default(self):
        with unittest.mock.patch("agent.devops.send_webhook_payload") as send_fn:
            notify("https://example.org/webhook", "J", "N", "s")
        send_fn.assert_not_called()

    def test_real_send_records_result(self):
        with unittest.mock.patch("agent.devops.send_webhook_payload",
                                 return_value={"status": "sent", "http_status": 200}):
            result = notify(
                "https://example.org/webhook", "JOB1", "JOB1", "summary", dry_run=False
            )
        self.assertEqual(result["status"], "sent")

    def test_real_send_failure_is_safe(self):
        with unittest.mock.patch("agent.devops.send_webhook_payload",
                                 return_value={"status": "error", "message": "failed"}):
            result = notify(
                "https://example.org/webhook", "JOB1", "JOB1", "summary", dry_run=False
            )
        self.assertEqual(result["status"], "error")
        self.assertIn("failed", result["message"])


if __name__ == "__main__":
    import unittest.mock  # noqa
    unittest.main()
else:
    import unittest.mock  # noqa: E402


class ExamplesNoSecretsTests(unittest.TestCase):
    """Acceptance criterion: examples contain no real secrets."""

    EXAMPLES = [
        "examples/config/ownership-rules.example.yaml",
        "examples/jenkins/Jenkinsfile.z-agent-example",
        "examples/github-actions/z-agent-mainframe-job-check.yml",
        "examples/api/job-summary-curl.sh",
        "examples/api/incident-summary-curl.sh",
        "examples/api/notify-dry-run-curl.sh",
    ]

    SUSPICIOUS = (
        "ghp_", "gho_", "AKIA", "-----BEGIN PRIVATE KEY",
        "xoxb-", "xoxp-", "real-token", "prod-password",
    )

    def test_examples_use_only_fake_values(self):
        import os
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for rel in self.EXAMPLES:
            path = os.path.join(base, rel)
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    text = handle.read()
            except FileNotFoundError:
                continue
            for token in self.SUSPICIOUS:
                self.assertNotIn(token, text, msg=f"{rel} contained '{token}'")
            # Any emails present must be @example.org, not real domains.
            import re
            for match in re.findall(r"[\w.+-]+@([\w.-]+\.\w+)", text):
                self.assertIn("example", match.lower(),
                              msg=f"{rel} contains non-example email domain '{match}'")