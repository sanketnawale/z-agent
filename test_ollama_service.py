"""Tests for the Ollama spool explanation service (agent.ollama_service).

Ollama is mocked - tests never require a running Ollama or IBM Z system.
"""

import unittest
from unittest import mock

from agent import ollama_service
from agent.masking import mask_spool_text


def _fake_response_ok(text: str):
    response = mock.Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"response": text}
    return response


def _fake_response_connection_error():
    def _tracker(*args, **kwargs):
        raise __import__("requests").exceptions.ConnectionError("no ollama")
    return _tracker


class OllamaServiceSuccessTests(unittest.TestCase):
    def _config(self):
        return {"ollama_url": "http://127.0.0.1:11434", "model": "llama3.2:3b"}

    def test_returns_structured_result_from_json(self):
        model_text = (
            '{"likely_cause": "Input dataset allocation failure", '
            '"evidence": "Spool contains dataset allocation message.", '
            '"suggested_next_step": "Verify the DD statement and dataset existence.", '
            '"confidence": "medium"}'
        )
        with mock.patch("agent.ollama_service.requests.post",
                        return_value=_fake_response_ok(model_text)) as posted:
            result = ollama_service.explain_spool_with_ollama(
                "IEFC621D ALLOCATION FAILED", ai_config=self._config(), job_id="JOB12345"
            )

        self.assertEqual(result["status"], "explained")
        # job_id is attached by the API layer, not the service core, so just
        # confirm the model used and required structured fields are present.
        for field in ("likely_cause", "evidence", "suggested_next_step", "confidence", "model", "ai_used"):
            self.assertIn(field, result)
        self.assertEqual(result["likely_cause"], "Input dataset allocation failure")
        self.assertEqual(result["evidence"], "Spool contains dataset allocation message.")
        self.assertEqual(result["suggested_next_step"],
                         "Verify the DD statement and dataset existence.")
        self.assertEqual(result["confidence"], "medium")
        self.assertTrue(result["ai_used"])
        self.assertEqual(result["model"], "llama3.2:3b")
        self.assertEqual(result["status"], "explained")

        # Confirm masking happened BEFORE the call: the prompt must carry no raw secret.
        sent_prompt = posted.call_args.kwargs["json"]["prompt"]
        self.assertIn("Masked spool output:", sent_prompt)

    def test_normalizes_invalid_confidence_to_low(self):
        model_text = (
            '{"likely_cause": "x", "evidence": "y", '
            '"suggested_next_step": "z", "confidence": "DEFINITELY"}'
        )
        with mock.patch("agent.ollama_service.requests.post",
                        return_value=_fake_response_ok(model_text)):
            result = ollama_service.explain_spool_with_ollama("body", ai_config=self._config())
        self.assertEqual(result["status"], "explained")
        self.assertEqual(result["confidence"], "low")

    def test_fallback_extract_from_balanced_json_with_surrounding_text(self):
        model_text = (
            "Here is the analysis:\n"
            '{"likely_cause": "JCL validation failed", "evidence": "IEFC660E on step 1", '
            '"suggested_next_step": "Fix the DD statement.", "confidence": "high"}\n'
            "Done."
        )
        with mock.patch("agent.ollama_service.requests.post",
                        return_value=_fake_response_ok(model_text)):
            result = ollama_service.explain_spool_with_ollama("body", ai_config=self._config())
        self.assertEqual(result["status"], "explained")
        self.assertEqual(result["likely_cause"], "JCL validation failed")
        self.assertEqual(result["confidence"], "high")
        self.assertTrue(result["ai_used"])

    def test_handles_empty_model_response(self):
        with mock.patch("agent.ollama_service.requests.post",
                        return_value=_fake_response_ok("")):
            result = ollama_service.explain_spool_with_ollama("body", ai_config=self._config())
        self.assertEqual(result["status"], "explained")
        self.assertTrue(result["ai_used"])
        self.assertIn("empty", result["likely_cause"].lower())


class OllamaServiceFailureTests(unittest.TestCase):
    def test_connection_failure_returns_safe_error(self):
        with mock.patch("agent.ollama_service.requests.post",
                        side_effect=_fake_response_connection_error()):
            result = ollama_service.explain_spool_with_ollama("body", ai_config={"ollama_url": "x"})
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "AI explanation is currently unavailable.")
        self.assertFalse(result["ai_used"])
        self.assertNotIn("exception", result)
        self.assertNotIn("traceback", result)

    def test_timeout_returns_safe_error(self):
        import requests
        with mock.patch("agent.ollama_service.requests.post",
                        side_effect=requests.exceptions.Timeout("timed out")):
            result = ollama_service.explain_spool_with_ollama("body", ai_config={"ollama_url": "x"})
        self.assertEqual(result["status"], "error")
        self.assertFalse(result["ai_used"])

    def test_http_error_returns_safe_error(self):
        resp = mock.Mock()
        resp.raise_for_status.side_effect = __import__("requests").exceptions.HTTPError("500")
        with mock.patch("agent.ollama_service.requests.post", return_value=resp):
            result = ollama_service.explain_spool_with_ollama("body", ai_config={"ollama_url": "x"})
        self.assertEqual(result["status"], "error")
        self.assertFalse(result["ai_used"])


class FullPipelineMaskingTests(unittest.TestCase):
    """The real pipeline is: raw spool -> mask_spool_text -> ollama_service."""

    def test_secret_is_masked_before_reaching_ollama(self):
        raw = "password=supersecret STEP1 IEFC621D ALLOCATION FAILED"
        masked = mask_spool_text(raw)
        self.assertNotIn("supersecret", masked)
        model_text = (
            '{"likely_cause": "allocation failure", "evidence": "IEFC621D", '
            '"suggested_next_step": "check DD", "confidence": "medium"}'
        )
        with mock.patch("agent.ollama_service.requests.post",
                        return_value=_fake_response_ok(model_text)) as posted:
            ollama_service.explain_spool_with_ollama(masked, ai_config={
                "ollama_url": "http://127.0.0.1:11434", "model": "llama3.2:3b"
            })
        prompt = posted.call_args.kwargs["json"]["prompt"]
        self.assertNotIn("supersecret", prompt)
        self.assertIn("<REDACTED>", prompt)


if __name__ == "__main__":
    unittest.main()