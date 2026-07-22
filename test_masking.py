"""Tests for the sensitive data masking utility (agent.masking)."""

import unittest

from agent.masking import contains_obvious_secrets, mask_spool_text


class MaskingTests(unittest.TestCase):
    def test_masks_email(self):
        self.assertNotIn("operator@bank.example.com",
                         mask_spool_text("Contact operator@bank.example.com for details"))
        self.assertIn("<EMAIL>", mask_spool_text("operator@bank.example.com"))

    def test_masks_ipv4(self):
        self.assertIn("<IP_ADDRESS>", mask_spool_text("Connected from 10.20.30.40"))

    def test_masks_password_assignment(self):
        masked = mask_spool_text("password=abc123")
        self.assertIn("password=<REDACTED>", masked)
        self.assertNotIn("abc123", masked)

    def test_masks_token_and_api_key_variants(self):
        for raw in (
            "token=secrettokendata",
            "API_KEY=mykeyvalue",
            "api-key: mykeyvalue",
            "SECRET: s3cr3tvalue",
        ):
            masked = mask_spool_text(raw)
            self.assertNotIn("secrettokendata", masked)
            self.assertNotIn("mykeyvalue", masked)
            self.assertNotIn("s3cr3tvalue", masked)
            self.assertIn("<REDACTED>", masked)

    def test_masks_url(self):
        masked = mask_spool_text("See https://internal.mfhost01:10443/zosmf")
        self.assertIn("<URL>", masked)
        self.assertNotIn("mfhost01", masked)

    def test_masks_hostname_assignment(self):
        masked = mask_spool_text("host=mvshost01.example.org")
        self.assertIn("<HOSTNAME_REDACTED>", masked)
        self.assertNotIn("mvshost01.example.org", masked)

    def test_masks_mainframe_dataset_name(self):
        masked = mask_spool_text("Allocation failed for USER01.PAYROLL.PROD.INPUT")
        self.assertIn("<DATASET_NAME>", masked)
        self.assertNotIn("USER01.PAYROLL.PROD.INPUT", masked)

    def test_does_not_mask_single_tokens(self):
        """Message codes / single uppercase tokens must remain visible to the AI."""
        raw = "IEFBR14 JESMSGLG IGYPS2113-E"
        masked = mask_spool_text(raw)
        self.assertIn("IEFBR14", masked)
        self.assertIn("JESMSGLG", masked)
        self.assertIn("IGYPS2113-E", masked)

    def test_masks_long_numeric_account_ids(self):
        masked = mask_spool_text("Account 1234567890 closed")
        self.assertIn("<ACCOUNT_ID>", masked)
        self.assertNotIn("1234567890", masked)

    def test_returns_empty_string_for_empty(self):
        self.assertEqual(mask_spool_text(""), "")

    def test_returns_string_for_non_string(self):
        self.assertEqual(mask_spool_text(None), "")
        self.assertEqual(mask_spool_text(123), "")

    def test_contains_obvious_secrets(self):
        self.assertTrue(contains_obvious_secrets("password=abc"))
        self.assertTrue(contains_obvious_secrets("from 1.2.3.4"))
        self.assertTrue(contains_obvious_secrets("me@example.com"))
        self.assertFalse(contains_obvious_secrets("IEFBR14 step ran fine"))
        self.assertFalse(contains_obvious_secrets(""))


if __name__ == "__main__":
    unittest.main()