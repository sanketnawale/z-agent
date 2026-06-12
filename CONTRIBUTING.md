# Contributing to Z-Agent

Thank you for your interest in contributing to Z-Agent.

Z-Agent is a browser-based MainframeOps assistant built with Zowe CLI, Python, Django, FastAPI, Docker, and pluggable AI providers.

The project goal is simple:

Zowe gives access. Z-Agent adds guidance.

## Project Principles

- Keep the project beginner-friendly.
- Keep IBM Z access based on Zowe.
- Keep AI as an explanation layer, not the source of truth.
- Prefer evidence-based diagnosis before AI explanation.
- Keep provider/model switching modular through the AI Gateway.
- Do not commit secrets, credentials, or local environment files.

## Development Setup

Create a local Python virtual environment:

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

Run with Docker:

    docker compose up -d --build

Check running containers:

    docker ps

Stop the environment:

    docker compose down

## Repository Hygiene

Do not commit:

- venv/
- .venv/
- __pycache__/
- .env
- zowe.config.json
- zowe.schema.json
- API keys
- passwords
- certificates
- local database files
- real production spool output

Use .env.example for example configuration only.

## Contribution Guidelines

- Keep pull requests small and focused.
- Explain what changed and why.
- Add or update documentation when adding features.
- Add screenshots for UI changes when possible.
- Test the change locally before opening a pull request.
- Do not introduce hardcoded credentials.
- Do not send raw sensitive mainframe data to AI providers.

## Areas for Contribution

Good first areas include:

- Documentation improvements
- Screenshots and demo examples
- Spool diagnosis patterns
- UI improvements
- AI Gateway provider improvements
- Dataset Explorer improvements
- USS Browser improvements
- Tests for diagnosis logic
- Docker and deployment improvements

## Pull Request Checklist

Before submitting a pull request, check:

- The app starts locally or with Docker.
- No secrets are committed.
- No virtual environment files are committed.
- Documentation is updated if needed.
- The change is clearly explained.

## Security

If you find a security issue, please do not open a public GitHub issue with sensitive details.

Report it privately to the maintainer.
