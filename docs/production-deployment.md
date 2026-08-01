# Z-Agent Production Deployment Notes

Z-Agent can be deployed behind Nginx with HTTPS. This document describes the
current public deployment shape for the `v1.2.0 – Production Readiness
Preview` and lists the safety rules that must hold for any real deployment.

## Current public deployment

| Component        | Value                                          |
|------------------|------------------------------------------------|
| Domain           | `https://zagent.cloudnova.tech`                |
| Container        | `z-agent`                                      |
| Frontend         | Django / Gunicorn on port `8001` (in container)|
| Backend          | FastAPI on `127.0.0.1:3001` (in container)    |
| AI runtime       | `z-agent-ollama` container                     |
| Reverse proxy    | Nginx                                          |
| TLS              | Let's Encrypt                                  |
| Health endpoint  | `GET /api/health` (frontend) and `GET /api/health` (backend) |

Both the frontend and backend expose `GET /api/health` returning
`{"status": "ok", "service": "...", "version": "v1.2.0-preview"}`. Use these
for Nginx `proxy_health`, load balancer health checks, and Docker
`healthcheck` (see `docker-compose.yml`).

## Required environment variables

Set these in the deployment environment (never commit them). See
`.env.example` for the canonical list.

```
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=<strong random value>
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,zagent.cloudnova.tech
DJANGO_CSRF_TRUSTED_ORIGINS=https://zagent.cloudnova.tech
DEFAULT_AI_PROVIDER=custom_ollama
DEFAULT_AI_MODEL=llama3.2:3b
DEFAULT_OLLAMA_URL=http://ollama:11434/api/generate
```

Generate a strong `DJANGO_SECRET_KEY` with:

```
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

## Bring up the stack

```
docker compose up -d --build
docker ps
docker logs --tail=100 z-agent
```

Verify health:

```
curl -fsS http://localhost:8001/api/health
curl -fsS http://localhost:8001/
```

The `/api/health` endpoint should return JSON with `"status": "ok"`. The root
path redirects to `/jobs/` (or `/setup/` when no session exists).

## Nginx reverse proxy notes (example)

```nginx
server {
    listen 443 ssl http2;
    server_name zagent.cloudnova.tech;

    ssl_certificate     /etc/letsencrypt/live/zagent.cloudnova.tech/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/zagent.cloudnova.tech/privkey.pem;

    client_max_body_size 10m;

    location / {
        proxy_pass         http://127.0.0.1:8001;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Forwarded-For    $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto  $scheme;
        proxy_read_timeout 360s;
    }
}

server {
    listen 80;
    server_name zagent.cloudnova.tech;
    return 301 https://$host$request_uri;
}
```

Django reads `X-Forwarded-Proto` because
`SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` is set in
`settings.py`.

## Important safety notes

- Do not commit IBM Z credentials.
- Do not commit `zowe.config.json`.
- Do not commit `.env`.
- Do not commit `db.sqlite3`.
- Use session-based credentials only — users enter IBM Z details on the
  setup page; they are stored in the browser session and cleared on logout.
- Keep AI explanations advisory. Z-Agent extracts facts in Python and asks
  the model to explain them; AI does not decide actions.
- Masking is mandatory before AI processing (see `agent/masking.py`).
- Audit logging is mandatory for write and AI actions (see `agent` /
  `jobs/audit.py`).
- Webhook `notify` defaults to `dry_run=true` so pipelines never accidentally
  make outbound calls.
- `JCL submit` and `DEVOPS_NOTIFY_SENT` are gated by the safety mode and
  require explicit approval in `EXECUTE` mode.

## Health endpoint reference

| Endpoint                | Auth        | Purpose                              |
|-------------------------|-------------|--------------------------------------|
| `GET /api/health`       | none        | Frontend process alive (Django)      |
| `GET /health`           | none        | Backend legacy health (FastAPI)      |
| `GET /api/health`       | none        | Backend versioned health (FastAPI)   |

Health endpoints intentionally do not record audit entries, because they are
called frequently by orchestrators.

## What is NOT production-ready yet

- `SECRET_KEY` must be supplied per environment before public deployment.
- No persistent database backend beyond SQLite — acceptable for this
  preview, must move to PostgreSQL or equivalent before scaling.
- No SSO / external auth — the setup page stores credentials in the session.
- Static asset hosting should move to a CDN or Nginx static root before
  large-scale use.
- No rate limiting in front of the AI endpoints (mitigated by the masking
  layer and the short Performance Insights timeout).

See `docs/release-checklist.md` and `docs/security-review-checklist.md` for
the full set of pre-release gates.