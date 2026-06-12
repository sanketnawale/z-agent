# Security Policy

Z-Agent is currently an MVP and demo-oriented project. It should not be used in production without proper security review.

## Current Security Model

- IBM Z credentials are not baked into the Docker image.
- Users enter their own IBM Z connection details in the setup page.
- Credentials are stored only in the current web session.
- Logout clears the session.
- The project avoids privileged SMF access in the current version.
- Local/server Ollama can be used to avoid sending explanations to cloud AI providers.
- Cloud AI providers are optional and require user-provided API keys.

## Do Not Commit

Never commit:

- `.env`
- `zowe.config.json`
- `zowe.schema.json`
- API keys
- passwords
- certificates
- private keys
- real spool output containing sensitive production data

## Reporting Security Issues

Please do not open public GitHub issues for sensitive security problems.

For now, report security concerns privately to the maintainer.
