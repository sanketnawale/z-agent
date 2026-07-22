# FAQ

> z-agent does not replace Zowe. It builds on Zowe/zOSMF.

Frequently asked questions, answered honestly and Open Mainframe-friendly.

## Is z-agent replacing Zowe?

No. z-agent builds **on** Zowe. Zowe CLI and z/OSMF are the access layer for
all z/OS operations. z-agent adds an AI-assisted, safe, auditable operations
layer on top — it never duplicates Zowe's access role. See
`docs/comparison-with-zowe.md`.

## Is z-agent production-ready?

No. z-agent is an early public preview and a Sandbox candidate, not a
production tool. It should not be used against production IBM Z systems without
a full security review. See `docs/known-limitations.md`.

## Does z-agent require IBM Z credentials?

z-agent itself does not store credentials. Users enter their own non-production
IBM Z credentials on the setup page; they live only in the web session. For
DevOps pipelines, credentials are passed via HTTP headers from your pipeline's
secret store (Jenkins credentials, GitHub secrets, etc.). See `SECURITY.md`.

## Does z-agent send data to external AI services?

By default, no. z-agent defaults to a **local Ollama** runtime so spool data
does not leave your environment. Cloud providers (Claude, OpenAI, Gemini) are
optional and require a user-provided API key. Either way, sensitive values are
masked before AI analysis. See `docs/ai-safety.md`.

## Why Ollama?

Ollama runs locally, is open-source-friendly, and lets teams explore
AI-assisted operations without sending sensitive spool data to the cloud. It
matches z-agent's local-first, safety-first design. Cloud providers remain
optional for teams that explicitly choose them.

## Can z-agent be used in DevOps pipelines?

Yes. z-agent exposes pipeline-friendly REST APIs:

- `POST /api/devops/job-summary` — structured summary with `safe_to_continue`
- `POST /api/devops/incident-summary` — paste-ready incident summary
- `POST /api/devops/notify` — webhook notification (dry-run by default)

Jenkins, GitHub Actions, and curl examples are included. See
`docs/devops-integration.md` and `docs/pipeline-examples.md`.

## Can z-agent notify responsible teams?

Partially. z-agent can map a job name to a recommended owner using simple
ownership rules (`examples/config/ownership-rules.example.yaml`) and surface
that in incident summaries. Webhook notifications support dry-run mode by
default; real sends are gated by the safety mode. See
`docs/incident-routing.md`.

## Can z-agent analyze SMF data?

Not yet. SMF analytics is a future direction, gated on authorized access and
an explicit safety model. Today z-agent focuses on jobs, spool, JCL,
datasets, and USS. See `ROADMAP.md` and `docs/known-limitations.md`.

## Can z-agent run in Kubernetes?

Kubernetes/Helm is a future roadmap item. Today z-agent ships Docker Compose
for local/server deployment. The Django + FastAPI split is already
container-friendly. See `ROADMAP.md`.

## Is AI output authoritative?

No. AI explanations are **advisory only**. z-agent never lets AI execute
actions on IBM Z, and it never lets AI decide job results. Python extracts the
facts; AI explains them. Treat AI output as a helpful first-pass, not a
verdict. See `docs/ai-safety.md`.

## How can I contribute?

- Read `CONTRIBUTING.md` and `GOVERNANCE.md`.
- Browse `docs/good-first-issues.md` for beginner-friendly tasks.
- Open issues/PRs using the templates in `.github/`.
- Do not commit secrets (see `SECURITY.md`).
- If you're a tester, see `TESTERS.md`.