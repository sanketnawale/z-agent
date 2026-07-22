"""
Sensitive data masking for IBM Z job spool output.

Before any spool text is sent to an AI model, z-agent scrubs values that could
reveal hostnames, account identifiers, credentials, or private dataset names.

The masking is intentionally conservative: when in doubt, mask the value and
replace it with a descriptive placeholder so the model can still reason about
the *structure* of the message without seeing the actual secret.

This module has no third-party dependencies and never raises on bad input -
unknown input is returned unchanged.
"""

from __future__ import annotations

import re
from typing import List, Tuple

MaskRule = Tuple[str, str]

# Ordered list of (compiled_regex, replacement). Order matters: we mask
# composite tokens (emails, URLs) before their sub-parts (hostnames, IPs) so
# the inner placeholders do not get double-masked in a confusing way.
_MASK_RULES: List[MaskRule] = []


def _add(pattern: str, replacement: str, flags: int = 0) -> None:
    _MASK_RULES.append((re.compile(pattern, flags), replacement))


# Email addresses e.g. operator@bank.example.com
_add(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", "<EMAIL>")

# Tokens / passwords / secrets assignments.
# Matches  key=value  or  key: value  for common secret-like keys.
_add(
    r"(?i)\b(password|passwd|pwd|secret|token|api[_\-]?key|access[_\-]?key|"
    r"auth[_\-]?token|bearer|credential|passphrase)\b\s*[:=]\s*"
    r"([^\s,;}\]\"']+)",
    r"\1=<REDACTED>",
)

# URLs - replace the whole URL but keep a placeholder so hosts inside it are hidden.
_add(r"\bhttps?://[^\s\"'<>]+", "<URL>")

# IPv4 addresses
_add(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "<IP_ADDRESS>")

# Hostname assignments e.g. HOST=mvshost01  /  host: mvshost01.example.org
_add(
    r"(?i)\bhost(?:name)?\b\s*[:=]\s*([A-Za-z0-9.\-]+)",
    "HOSTNAME=<HOSTNAME_REDACTED>",
)

# IBM Z / mainframe dataset names: uppercase, dot-separated, at least one dot.
# Segments are alphanumeric plus @ # $ - and overall length is realistic.
# A single token (no dot) is intentionally NOT matched so message codes such
# as IEFBR14 or JESMSGLG remain visible to the model.
_add(
    r"\b[A-Z@$#][A-Z0-9@$#\-]{0,7}(?:\.[A-Z@$#][A-Z0-9@$#\-]{0,7}){1,5}\b",
    "<DATASET_NAME>",
)

# Long numeric / account-like identifiers: runs of 8+ digits.
_add(r"\b\d{8,}\b", "<ACCOUNT_ID>")


def mask_spool_text(text: str) -> str:
    """Return a copy of *text* with sensitive values replaced by placeholders.

    Always returns a str. Non-string / falsy input is returned unchanged.
    """
    if not isinstance(text, str) or not text:
        return text if isinstance(text, str) else ""

    masked = text
    for regex, replacement in _MASK_RULES:
        masked = regex.sub(replacement, masked)
    return masked


def contains_obvious_secrets(text: str) -> bool:
    """Quick check used by tests and audit logging to confirm masking is needed."""
    if not isinstance(text, str) or not text:
        return False
    probe_keywords = ("password", "passwd", "pwd=", "secret", "token", "api_key", "apikey")
    lower = text.lower()
    if any(k in lower for k in probe_keywords):
        return True
    if re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text):
        return True
    if re.search(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", text):
        return True
    return False