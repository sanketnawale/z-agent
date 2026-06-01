import os
import requests
from fastapi import HTTPException


ALLOWED_PROVIDERS = {
    "rule_based",
    "server_ollama",
    "custom_ollama",
    "claude",
    "openai",
    "gemini",
}


def normalize_ai_config(config: dict | None) -> dict:
    config = config or {}

    provider = (config.get("provider") or "server_ollama").strip()
    model = (config.get("model") or "").strip()
    api_key = (config.get("api_key") or "").strip()
    ollama_url = (config.get("ollama_url") or "").strip()

    if provider not in ALLOWED_PROVIDERS:
        provider = "rule_based"

    if provider in {"server_ollama", "custom_ollama"}:
        model = model or "llama3.2:3b"
        ollama_url = ollama_url or "http://127.0.0.1:11434/api/generate"

    if provider == "claude":
        model = model or "claude-3-5-haiku-latest"

    if provider == "openai":
        model = model or "gpt-4.1-mini"
    
    if provider == "gemini":
        model = model or "gemini-2.5-flash"

    return {
        "provider": provider,
        "model": model,
        "api_key": api_key,
        "ollama_url": ollama_url,
    }


def explain_with_ai(prompt: str, ai_config: dict | None = None) -> dict:
    config = normalize_ai_config(ai_config)
    provider = config["provider"]

    if provider == "rule_based":
        return {
            "provider": "rule_based",
            "model": "none",
            "response": (
                "AI is disabled. Z-Agent is showing the deterministic rule-based "
                "diagnosis only. Change AI Settings to use Ollama, Claude, or OpenAI."
            ),
        }

    if provider in {"server_ollama", "custom_ollama"}:
        return explain_with_ollama(prompt, config)

    if provider == "claude":
        return explain_with_claude(prompt, config)

    if provider == "openai":
        return explain_with_openai(prompt, config)
    
    if provider == "gemini":
        return explain_with_gemini(prompt, config)

    return {
        "provider": "rule_based",
        "model": "none",
        "response": "Unsupported AI provider. Rule-based mode only.",
    }


def explain_with_ollama(prompt: str, config: dict) -> dict:
    try:
        response = requests.post(
            config["ollama_url"],
            json={
                "model": config["model"],
                "prompt": prompt,
                "stream": False,
                "keep_alive": "15m",
                "options": {"temperature": 0.2},
            },
            timeout=(10, 300),
        )
        response.raise_for_status()
        data = response.json()

        return {
            "provider": config["provider"],
            "model": config["model"],
            "response": data.get("response", "").strip() or "Ollama returned an empty response.",
        }

    except requests.exceptions.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Ollama provider failed: {exc}")


def explain_with_claude(prompt: str, config: dict) -> dict:
    if not config["api_key"]:
        raise HTTPException(status_code=400, detail="Claude API key is missing.")

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": config["api_key"],
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": config["model"],
                "max_tokens": 900,
                "temperature": 0.2,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=180,
        )
        response.raise_for_status()
        data = response.json()

        text = ""
        for part in data.get("content", []):
            if part.get("type") == "text":
                text += part.get("text", "")

        return {
            "provider": "claude",
            "model": config["model"],
            "response": text.strip() or "Claude returned an empty response.",
        }

    except requests.exceptions.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Claude provider failed: {exc}")


def explain_with_openai(prompt: str, config: dict) -> dict:
    if not config["api_key"]:
        raise HTTPException(status_code=400, detail="OpenAI API key is missing.")

    try:
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {config['api_key']}",
                "Content-Type": "application/json",
            },
            json={
                "model": config["model"],
                "input": prompt,
                "temperature": 0.2,
                "max_output_tokens": 900,
            },
            timeout=180,
        )
        response.raise_for_status()
        data = response.json()

        text = data.get("output_text", "")
        if not text:
            chunks = []
            for item in data.get("output", []):
                for content in item.get("content", []):
                    if content.get("type") in {"output_text", "text"}:
                        chunks.append(content.get("text", ""))
            text = "\n".join(chunks)

        return {
            "provider": "openai",
            "model": config["model"],
            "response": text.strip() or "OpenAI returned an empty response.",
        }

    except requests.exceptions.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI provider failed: {exc}")
    
def explain_with_gemini(prompt: str, config: dict) -> dict:
    if not config["api_key"]:
        raise HTTPException(status_code=400, detail="Gemini API key is missing.")

    try:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/"
            f"models/{config['model']}:generateContent"
        )

        response = requests.post(
            url,
            params={"key": config["api_key"]},
            json={
                "contents": [
                    {
                        "role": "user",
                        "parts": [
                            {"text": prompt}
                        ],
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 900,
                },
            },
            timeout=180,
        )
        response.raise_for_status()
        data = response.json()

        text_parts = []
        for candidate in data.get("candidates", []):
            content = candidate.get("content", {})
            for part in content.get("parts", []):
                if "text" in part:
                    text_parts.append(part["text"])

        return {
            "provider": "gemini",
            "model": config["model"],
            "response": "\n".join(text_parts).strip() or "Gemini returned an empty response.",
        }

    except requests.exceptions.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Gemini provider failed: {exc}")