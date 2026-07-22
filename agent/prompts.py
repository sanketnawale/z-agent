"""
Prompt templates for AI-assisted IBM Z spool explanation.

The prompt is deliberately constrained:

- It only ever sees *masked* spool text.
- It asks for a strict JSON object so the result can be turned into a
  structured response without fragile free-text parsing.
- It forbids destructive actions and refuses to invent missing facts.

This module has no third-party dependencies.
"""

from __future__ import annotations

SYSTEM_INSTRUCTIONS = """You are z-agent, an AI-assisted IBM Z operations helper.

Analyze the following masked IBM Z job spool output.

Return:
1. likely cause
2. evidence from the spool
3. suggested next step
4. confidence: low, medium, or high

Do not recommend destructive actions.
Do not invent missing facts.
If the spool does not contain enough evidence, say so clearly.
Do not expose or request secrets.
Do not recommend bypassing security controls.
AI explanations are advisory only and must not replace mainframe experts or
production change controls.

Respond with ONLY a JSON object using exactly these keys:
{
  "likely_cause": "...",
  "evidence": "...",
  "suggested_next_step": "...",
  "confidence": "low | medium | high"
}

Do not include any text before or after the JSON object."""


def build_spool_explanation_prompt(masked_spool_text: str, job_id: str | None = None) -> str:
    """Build a safe, structured prompt for the masked spool explanation task."""
    job_line = f"Job ID: {job_id}\n" if job_id else ""
    safe_spool = masked_spool_text if masked_spool_text is not None else ""
    safe_spool = safe_spool if isinstance(safe_spool, str) else str(safe_spool)

    return (
        f"{SYSTEM_INSTRUCTIONS}\n\n"
        f"{job_line}"
        f"Masked spool output:\n"
        f"{safe_spool}\n"
    )


PERFORMANCE_INSIGHTS_SYSTEM_INSTRUCTIONS = """You are z-agent, an AI-assisted IBM Z performance operations helper.

Analyze the provided mainframe performance insights report. The report was
calculated from statistical metrics using local/demo thresholds; it is NOT a
comparison against an external benchmark population.

Rules:
- Explain the ratios in operations-friendly language.
- Do NOT claim real benchmark comparison unless benchmark data is explicitly provided.
- Do NOT recommend destructive actions.
- Suggest safe, advisory next steps.
- Clearly say when the input is insufficient.
- Treat all output as advisory only and do not replace mainframe experts.
- Do not invent facts or numbers that are not in the report.

Respond with ONLY a JSON object using exactly these keys:
{
  "summary": "...",
  "key_findings": ["..."],
  "possible_optimization_areas": ["..."],
  "safe_next_steps": ["..."],
  "limitations": "..."
}

Do not include any text before or after the JSON object."""


def build_performance_insights_prompt(report_json: str) -> str:
    """Build a safe, structured prompt for the performance insights report.

    ``report_json`` should be a JSON string of the structured report produced
    by ``agent.performance_insights.build_performance_insights_report``.
    """
    safe = report_json if isinstance(report_json, str) else str(report_json or "")
    return (
        f"{PERFORMANCE_INSIGHTS_SYSTEM_INSTRUCTIONS}\n\n"
        f"Performance insights report (JSON):\n{safe}\n"
    )