"""
Ollama explanation service for AI-assisted spool analysis.

This service:

- builds a safe prompt from already-masked spool text
- calls a local Ollama runtime
- parses the model response into a structured result
- never raises - any failure returns a safe error dictionary

Expected environment variables (mirroring the rest of z-agent):

    OLLAMA_BASE_URL   base URL of the local Ollama runtime, e.g.
                      http://127.0.0.1:11434  (the /api/generate path is
                      appended automatically when not present)
    OLLAMA_MODEL      model tag, e.g. llama3.2:3b

A caller-supplied ai_config dict overrides the environment defaults and is
used by the FastAPI layer where the model/URL come from the Django AI profile.

This module depends only on the standard library plus `requests`.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict

import requests

from .prompts import build_spool_explanation_prompt

_VALID_CONFIDENCE = {"low", "medium", "high"}

# How long we wait for a connection / response from Ollama before giving up.
_CONNECT_TIMEOUT = 10
_READ_TIMEOUT = 120

_SAFE_ERROR = {
    "status": "error",
    "message": "AI explanation is currently unavailable.",
    "ai_used": False,
}


def _resolve_ollama_url(default_or_config: str) -> str:
    url = (default_or_config or "").strip()
    if not url:
        url = os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_URL") or "http://127.0.0.1:11434"
    if "/api/generate" not in url:
        url = url.rstrip("/") + "/api/generate"
    return url


def _resolve_model(default_or_config: str) -> str:
    model = (default_or_config or "").strip()
    if not model:
        model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    return model


def _ai_config_value(ai_config: Dict[str, Any] | None, key: str) -> str:
    if ai_config is None:
        return ""
    value = ai_config.get(key, "") or ""
    return str(value).strip()


def explain_spool_with_ollama(
    masked_spool_text: str,
    ai_config: Dict[str, Any] | None = None,
    job_id: str | None = None,
) -> Dict[str, Any]:
    """Call Ollama with a masked spool and return a structured explanation.

    Never raises. On any problem it returns the safe error dictionary so the
    calling web app stays up and the user only sees a generic message.
    """
    try:
        model = _ai_config_value(ai_config, "model") or _resolve_model("")
        ollama_url = _ai_config_value(ai_config, "ollama_url") or _resolve_ollama_url("")

        prompt = build_spool_explanation_prompt(masked_spool_text, job_id=job_id)

        response = requests.post(
            ollama_url,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "keep_alive": "15m",
                "options": {"temperature": 0.2},
            },
            timeout=(_CONNECT_TIMEOUT, _READ_TIMEOUT),
        )
        response.raise_for_status()
        data = response.json()
        raw_text = (data.get("response") or "").strip()
        if not raw_text:
            raw_text = "Ollama returned an empty response."
    except requests.exceptions.RequestException:
        return dict(_SAFE_ERROR)
    except Exception:
        return dict(_SAFE_ERROR)

    parsed = _parse_structured_response(raw_text)
    return {
        "status": "explained",
        "likely_cause": parsed["likely_cause"],
        "evidence": parsed["evidence"],
        "suggested_next_step": parsed["suggested_next_step"],
        "confidence": parsed["confidence"],
        "ai_used": True,
        "model": model,
    }


def _parse_structured_response(raw_text: str) -> Dict[str, str]:
    """Extract the structured fields from the model response with safe fallbacks."""
    likely_cause = ""
    evidence = ""
    suggested_next_step = ""
    confidence = "low"

    decoded = _try_parse_json(raw_text)
    if decoded is not None:
        likely_cause = str(decoded.get("likely_cause") or "").strip()
        evidence = str(decoded.get("evidence") or "").strip()
        suggested_next_step = str(decoded.get("suggested_next_step")
                                  or decoded.get("next_step") or "").strip()
        confidence = str(decoded.get("confidence") or "low").strip().lower()

    if not likely_cause:
        likely_cause, evidence, suggested_next_step, confidence = _fallback_parse(raw_text)

    if confidence not in _VALID_CONFIDENCE:
        confidence = "low"

    if not likely_cause:
        likely_cause = raw_text.strip() or "Unable to determine likely cause from the provided spool output."
    if not evidence:
        evidence = "No explicit evidence was available in the masked spool output."
    if not suggested_next_step:
        suggested_next_step = "Inspect JESMSGLG, JESJCL, and JESYSMSG sections for more detail."

    return {
        "likely_cause": likely_cause,
        "evidence": evidence,
        "suggested_next_step": suggested_next_step,
        "confidence": confidence,
    }


def _try_parse_json(raw_text: str):
    """Try to decode a JSON object embedded anywhere in raw_text."""
    if not raw_text:
        return None
    try:
        return json.loads(raw_text)
    except (ValueError, TypeError):
        pass
    candidate = _extract_balanced_object(raw_text)
    if candidate is None:
        return None
    try:
        return json.loads(candidate)
    except (ValueError, TypeError):
        return None


def _extract_balanced_object(raw_text: str):
    """Return the first balanced {...} substring, or None."""
    start = raw_text.find("{")
    if start == -1:
        return None
    depth = 0
    for idx in range(start, len(raw_text)):
        ch = raw_text[idx]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return raw_text[start:idx + 1]
    return None


_FALLBACK_PATTERNS = [
    ("likely_cause", re.compile(r"(?is)\b1\.?\s*likely\s*cause\b[:\-]?\s*(.*?)(?=\n\s*\d?\.?\s*(evidence|suggested|next|confidence|$))")),
    ("evidence", re.compile(r"(?is)\b2\.?\s*evidence\b[:\-]?\s*(.*?)(?=\n\s*\d?\.?\s*(suggested|next|confidence|$))")),
    ("suggested_next_step", re.compile(r"(?is)\b3\.?\s*suggested\s*next\s*step\b[:\-]?\s*(.*?)(?=\n\s*\d?\.?\s*confidence\b|$)")),
    ("confidence", re.compile(r"(?is)\b4\.?\s*confidence\b[:\-]?\s*(low|medium|high)\b")),
]


def _fallback_parse(raw_text: str):
    """Last-resort parser for labelled numbered sections when JSON parsing fails."""
    fields = {"likely_cause": "", "evidence": "", "suggested_next_step": "", "confidence": ""}
    for name, pattern in _FALLBACK_PATTERNS:
        m = pattern.search(raw_text)
        if m:
            value = m.group(1).strip()
            value = re.sub(r"\s+", " ", value)
            fields[name] = value[:500]
    return (
        fields["likely_cause"],
        fields["evidence"],
        fields["suggested_next_step"],
        fields["confidence"] or "low",
    )