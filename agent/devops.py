"""
DevOps integration helpers for z-agent (v0.5.0 DevOps Integration Preview).

These utilities support pipeline-friendly IBM Z job summaries, incident
summaries, ownership routing, and dry-run webhook notifications. They are
intentionally framework-agnostic so they can be unit-tested without a running
IBM Z system, Ollama, or real webhook.

Key responsibilities:

- ownership routing: map a job name to a team/notify config from rules
- job summary: turn a diagnosis (+ optional AI explanation) into a structured,
  pipeline-ready JSON response with ``safe_to_continue``
- incident summary: build a paste-ready incident first-pass summary
- notify: build a webhook payload and, in dry-run mode, never touch the network

This module depends only on the standard library (``fnmatch``) and falls back
gracefully if ``yaml`` is unavailable for ownership-rule parsing.
"""

from __future__ import annotations

import fnmatch
import os
from typing import Any, Dict, List, Optional

try:  # optional dependency; a simple parser is used as fallback
    import yaml  # type: ignore
    _HAS_YAML = True
except Exception:  # pragma: no cover - fallback path
    _HAS_YAML = False

UNKNOWN_OWNER = "Unknown - configure ownership rules"


# ---------------------------------------------------------------------------
# Ownership routing
# ---------------------------------------------------------------------------

def load_ownership_rules(path: str) -> List[Dict[str, Any]]:
    """Load ownership rules from a YAML file.

    Returns an empty list on any error so callers never crash. Supports the
    documented ``ownership_rules`` list format (each item has ``job_pattern``,
    ``team``, and an optional ``notify`` mapping).
    """
    if not path or not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError:
        return []

    if _HAS_YAML:
        try:
            data = yaml.safe_load(text) or {}
        except Exception:
            return _parse_simple_ownership_rules(text)
        rules = data.get("ownership_rules", []) if isinstance(data, dict) else []
        if not isinstance(rules, list):
            return []
        return [r for r in rules if isinstance(r, dict)]

    return _parse_simple_ownership_rules(text)


def _parse_simple_ownership_rules(text: str) -> List[Dict[str, Any]]:
    """Minimal line-based parser for the documented ownership-rules format.

    Only handles the simple, predictable structure used by the example file.
    """
    rules: List[Dict[str, Any]] = []
    current: Optional[Dict[str, Any]] = None
    in_notify = False

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped == "-":
            if current:
                rules.append(current)
            current = {"notify": {}}
            in_notify = False
            continue

        key, sep, value = stripped.partition(":")
        if not sep:
            continue
        key = key.strip().lstrip("-").strip()
        value = value.strip().strip('"').strip("'")

        if current is None:
            current = {"notify": {}}

        if key == "job_pattern":
            current["job_pattern"] = value
            in_notify = False
        elif key == "team":
            current["team"] = value
            in_notify = False
        elif key == "notify":
            in_notify = True
        elif in_notify and key in ("email", "webhook"):
            current.setdefault("notify", {})[key] = value
        else:
            in_notify = False

    if current:
        rules.append(current)

    return rules


def match_owner(job_name: str, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Return the ownership entry (team + notify) for ``job_name``.

    If no rule matches, returns ``{"team": UNKNOWN_OWNER, "notify": {}}``.
    Matching uses ``fnmatch`` wildcards so ``"PAY*"`` matches ``"PAYROLL01"``.
    Never raises; bad input yields the unknown-owner fallback.
    """
    if not job_name or not isinstance(job_name, str):
        return {"team": UNKNOWN_OWNER, "notify": {}}
    if not rules or not isinstance(rules, list):
        return {"team": UNKNOWN_OWNER, "notify": {}}

    name_upper = job_name.upper()
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        pattern = str(rule.get("job_pattern", "")).strip()
        if not pattern:
            continue
        if fnmatch.fnmatch(name_upper, pattern.upper()):
            return {
                "team": str(rule.get("team", UNKNOWN_OWNER)),
                "notify": dict(rule.get("notify", {}) or {}),
            }

    return {"team": UNKNOWN_OWNER, "notify": {}}


# ---------------------------------------------------------------------------
# Job summary
# ---------------------------------------------------------------------------

def _status_from_severity(severity: str) -> str:
    mapping = {
        "error": "FAILED",
        "success": "SUCCESS",
        "warning": "WARNING",
        "info": "ACTIVE",
    }
    return mapping.get(str(severity).lower(), "UNKNOWN")


def _result_from_status(status: str) -> str:
    mapping = {
        "FAILED": "failure",
        "SUCCESS": "success",
        "WARNING": "warning",
        "ACTIVE": "active",
        "UNKNOWN": "unknown",
    }
    return mapping.get(str(status), "unknown")


def _safe_to_continue(status: str) -> bool:
    """A pipeline may continue only when the job clearly succeeded."""
    return str(status).upper() == "SUCCESS"


def _format_return_code(final_rc: str) -> str:
    rc = str(final_rc or "").strip()
    if not rc or rc.upper() == "UNKNOWN":
        return "UNKNOWN"
    if rc.upper().startswith("RC="):
        return rc.upper()
    return f"RC={rc}"


def build_job_summary(
    job_id: str,
    job_name: str,
    diagnosis: Dict[str, Any],
    ai_explanation: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a structured, pipeline-ready job summary.

    ``diagnosis`` is the output of ``diagnose_spool`` in ``main.py``.
    ``ai_explanation`` is the optional output of
    ``explain_spool_with_ollama`` (already masked/structured).
    """
    severity = str(diagnosis.get("severity", "info")).lower()
    status = _status_from_severity(severity)
    return_code = _format_return_code(diagnosis.get("final_rc", "Unknown"))
    result = _result_from_status(status)

    likely_cause = str(diagnosis.get("headline", "")) or str(diagnosis.get("root_cause", ""))
    evidence_lines = diagnosis.get("evidence", [])
    evidence = "; ".join(str(e) for e in evidence_lines) if evidence_lines else ""
    suggested_next_step = str(diagnosis.get("fix", ""))

    ai_used = False
    confidence = "low"

    if ai_explanation and ai_explanation.get("ai_used"):
        ai_used = True
        confidence = str(ai_explanation.get("confidence", "low")).lower()
        if confidence not in ("low", "medium", "high"):
            confidence = "low"
        if ai_explanation.get("likely_cause"):
            likely_cause = str(ai_explanation["likely_cause"])
        if ai_explanation.get("evidence"):
            evidence = str(ai_explanation["evidence"])
        if ai_explanation.get("suggested_next_step"):
            suggested_next_step = str(ai_explanation["suggested_next_step"])

    return {
        "job_id": str(job_id or ""),
        "job_name": str(job_name or diagnosis.get("jobname", "")),
        "status": status,
        "return_code": return_code,
        "result": result,
        "likely_cause": likely_cause or "Unable to determine likely cause.",
        "evidence": evidence or "No explicit evidence was available.",
        "suggested_next_step": suggested_next_step or "Inspect spool output for more detail.",
        "confidence": confidence,
        "ai_used": ai_used,
        "safe_to_continue": _safe_to_continue(status),
    }


# ---------------------------------------------------------------------------
# Incident summary
# ---------------------------------------------------------------------------

def _severity_for_incident(status: str, diagnosis: Dict[str, Any]) -> str:
    upper = str(status).upper()
    if upper == "FAILED":
        text = f"{diagnosis.get('headline', '')} {diagnosis.get('root_cause', '')}".upper()
        return "high" if "ABEND" in text else "medium"
    if upper == "WARNING":
        return "low"
    if upper == "SUCCESS":
        return "low"
    return "low"


def build_incident_summary(
    job_id: str,
    job_name: str,
    diagnosis: Dict[str, Any],
    ai_explanation: Optional[Dict[str, Any]] = None,
    ownership: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a paste-ready incident first-pass summary."""
    severity_str = str(diagnosis.get("severity", "info")).lower()
    status = _status_from_severity(severity_str)
    return_code = _format_return_code(diagnosis.get("final_rc", "Unknown"))

    owner = ownership or {"team": UNKNOWN_OWNER, "notify": {}}
    recommended_owner = owner.get("team", UNKNOWN_OWNER)

    summary = str(diagnosis.get("headline", "")) or str(diagnosis.get("root_cause", ""))
    evidence_lines = diagnosis.get("evidence", [])
    evidence = "; ".join(str(e) for e in evidence_lines) if evidence_lines else ""
    suggested_next_step = str(diagnosis.get("fix", ""))

    if ai_explanation and ai_explanation.get("ai_used"):
        if ai_explanation.get("likely_cause"):
            summary = str(ai_explanation["likely_cause"])
        if ai_explanation.get("evidence"):
            evidence = str(ai_explanation["evidence"])
        if ai_explanation.get("suggested_next_step"):
            suggested_next_step = str(ai_explanation["suggested_next_step"])

    title = f"IBM Z job {job_name or job_id or 'Unknown'} failed with {return_code}"
    if status == "SUCCESS":
        title = f"IBM Z job {job_name or job_id} completed successfully ({return_code})"

    return {
        "title": title,
        "severity": _severity_for_incident(status, diagnosis),
        "summary": summary or "Unable to determine cause from available spool evidence.",
        "evidence": evidence or "No explicit evidence was available in the spool output.",
        "recommended_owner": recommended_owner,
        "suggested_next_step": suggested_next_step or "Inspect spool output for more detail.",
    }


# ---------------------------------------------------------------------------
# Webhook notification
# ---------------------------------------------------------------------------

def build_notify_payload(
    webhook_url: str,
    job_id: str,
    job_name: str,
    summary: str,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the JSON payload that would be POSTed to a webhook.

    Never includes secrets. The payload is safe to log in dry-run mode.
    """
    payload = {
        "job_id": str(job_id or ""),
        "job_name": str(job_name or ""),
        "summary": str(summary or ""),
        "source": "z-agent",
    }
    if extra and isinstance(extra, dict):
        for key, value in extra.items():
            if key not in ("token", "secret", "password", "api_key"):
                payload[key] = value
    return payload


def send_webhook_payload(webhook_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Send a webhook payload. Returns a status dict, never raises.

    Importing ``requests`` lazily keeps this module importable in environments
    without ``requests`` and keeps the dry-run path network-free.
    """
    if not webhook_url or not str(webhook_url).strip():
        return {"status": "error", "message": "No webhook URL provided."}

    try:
        import requests
    except Exception:
        return {"status": "error", "message": "Webhook notification is currently unavailable."}

    try:
        response = requests.post(
            str(webhook_url).strip(),
            json=payload,
            timeout=(10, 30),
        )
        if response.status_code >= 400:
            return {
                "status": "error",
                "message": "Webhook returned an error status.",
                "http_status": response.status_code,
            }
        return {"status": "sent", "http_status": response.status_code}
    except Exception:
        return {"status": "error", "message": "Webhook notification failed."}


def notify(
    webhook_url: str,
    job_id: str,
    job_name: str,
    summary: str,
    dry_run: bool = True,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build (and optionally send) a webhook notification.

    Default ``dry_run=True`` never touches the network and returns the payload
    that would be sent. This is the safety default for DevOps pipelines.
    """
    payload = build_notify_payload(webhook_url, job_id, job_name, summary, extra=extra)

    if dry_run:
        return {
            "status": "dry_run",
            "message": "Notification payload generated but not sent.",
            "payload": payload,
        }

    send_result = send_webhook_payload(webhook_url, payload)
    send_result["payload"] = payload
    return send_result