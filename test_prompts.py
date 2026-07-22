"""Tests for the spool explanation prompt builder (agent.prompts)."""

import unittest

from agent.prompts import SYSTEM_INSTRUCTIONS, build_spool_explanation_prompt


class PromptBuilderTests(unittest.TestCase):
    def test_prompt_contains_safety_instructions(self):
        prompt = build_spool_explanation_prompt("IEFC621D ALLOCATION FAILED", job_id="J123")
        self.assertIn("z-agent", prompt)
        self.assertIn("Do not recommend destructive actions", prompt)
        self.assertIn("Do not invent missing facts", prompt)
        self.assertIn("advisory only", prompt)

    def test_prompt_includes_masked_spool(self):
        prompt = build_spool_explanation_prompt("masked spool body", job_id="J123")
        self.assertIn("Masked spool output:", prompt)
        self.assertIn("masked spool body", prompt)

    def test_prompt_includes_job_id_when_provided(self):
        prompt = build_spool_explanation_prompt("body", job_id="JOB999")
        self.assertIn("Job ID: JOB999", prompt)

    def test_prompt_omits_job_id_when_missing(self):
        prompt = build_spool_explanation_prompt("body")
        self.assertNotIn("Job ID:", prompt)

    def test_prompt_requests_json_format(self):
        prompt = build_spool_explanation_prompt("body")
        self.assertIn("likely_cause", prompt)
        self.assertIn("evidence", prompt)
        self.assertIn("suggested_next_step", prompt)
        self.assertIn("confidence", prompt)

    def test_system_instructions_immutable_core_rules(self):
        # Guard against accidentally dropping the safety wording.
        self.assertIn("low, medium, or high", SYSTEM_INSTRUCTIONS)
        self.assertIn("bypassing security", SYSTEM_INSTRUCTIONS)


if __name__ == "__main__":
    unittest.main()