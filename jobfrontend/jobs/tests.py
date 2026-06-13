from django.test import SimpleTestCase

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

    def test_mask_secret(self):
        self.assertEqual(mask_secret("abcd"), "****")
        self.assertEqual(mask_secret("abcdef"), "ab****ef")

    def test_mask_text_masks_sensitive_lines(self):
        text = "normal line\npassword=hello\nanother line"
        masked = mask_text(text)
        self.assertIn("normal line", masked)
        self.assertIn("[MASKED_SECRET_LINE]", masked)
        self.assertIn("another line", masked)
