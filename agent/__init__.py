"""
Z-Agent AI operations package.

Contains the helpers used by the AI-assisted spool explanation workflow:

- masking.mask_spool_text        : scrub sensitive values before AI analysis
- prompts.build_spool_explanation_prompt : build a safe, structured prompt
- ollama_service.explain_spool_with_ollama : call Ollama and return a structured result

These modules are intentionally framework-agnostic so they can be reused by the
FastAPI backend and covered by unit tests without a running IBM Z system.
"""

__all__ = ["masking", "prompts", "ollama_service"]