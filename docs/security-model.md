# Z-Agent Security Model

Z-Agent is currently an MVP and public-preview project. It is not production-ready without security review.

## Current Principles

- Do not bake IBM Z credentials into the image.
- Use session-based IBM Z profiles.
- Logout clears the session.
- Keep AI provider configuration session-based.
- Prefer local/server Ollama when sensitive data should not leave the environment.
- Do not commit secrets or real production spool data.
- Risky actions should pass through safety checks.
- Important actions should be written to the audit log.

## Safety Modes

Z-Agent supports three safety modes.

### READ_ONLY

Default and safest mode.

Allowed:

- View jobs
- View spool
- View datasets
- View USS
- Request AI explanations

Blocked:

- Submit JCL
- Cancel jobs
- Delete datasets
- Write USS files

### APPROVAL_REQUIRED

Risky actions require explicit approval before execution.

Example:

- First request returns approval required.
- User confirms.
- Second request includes approval flag.
- Action can proceed and is logged.

### EXECUTE

Risky actions can execute directly.

This mode should only be used in trusted demo, lab, or development environments.

## Audit Logging

Z-Agent records important actions such as:

- VIEW_JOBS
- VIEW_SPOOL
- VIEW_DATASET
- VIEW_USS
- AI_EXPLAIN
- SUBMIT_JCL
- CHANGE_SAFETY_MODE

Audit log records include:

- timestamp
- username
- action
- target
- safety mode
- status
- details

## Secret Masking

Audit logs should not store secrets.

Sensitive lines containing terms like password, token, secret, api_key, or authorization are masked before writing to audit logs.

## Current Limitations

- No role-based access control yet.
- No persistent enterprise identity integration yet.
- Approval flow is basic.
- Audit logs are stored in the local Django database.
- Production use requires additional security review.
