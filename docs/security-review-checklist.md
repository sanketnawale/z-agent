# Security Review Checklist

> z-agent does not replace Zowe. It builds on Zowe/zOSMF.

Use this checklist before any z-agent release or external review. It is not a
substitute for a formal security audit, but it captures the controls the
project enforces today.

## Secrets

- [ ] `.env` is not tracked (`git check-ignore -v .env`)
- [ ] `zowe.config.json` is not tracked
- [ ] `zowe.schema.json` is not tracked
- [ ] `db.sqlite3` / `*.sqlite3` are not tracked
- [ ] No API keys, tokens, passwords, or private keys in the diff
- [ ] No real IBM Z credentials in the diff
- [ ] Examples use `example.org` domains only
- [ ] A test asserts examples contain no real secrets (test_devops)

## Credentials

- [ ] Credentials are not baked into the Docker image
- [ ] Users enter credentials only on the setup page
- [ ] Credentials live only in the web session (logout clears them)
- [ ] DevOps pipelines pass credentials via headers, never hardcoded

## Audit logs

- [ ] Audit logs do not store raw spool text (metadata only)
- [ ] Audit details include action, job ID, AI used, model, safety mode, status
- [ ] `Details` fields are run through `mask_text` as defense in depth
- [ ] Tests assert raw spool is not stored in audit logs

## AI prompt safety

- [ ] AI prompts forbid destructive actions
- [ ] AI prompts forbid inventing missing facts
- [ ] AI prompts forbid requesting/exposing secrets
- [ ] AI prompts request a strict JSON object (no free-text parsing fragility)
- [ ] Confidence is normalized to low/medium/high

## Masking

- [ ] Spool text is masked before AI analysis (agent/masking.py)
- [ ] Masking covers emails, IPs, passwords/tokens/api_keys, URLs, host=
      assignments, dataset names, long numeric IDs
- [ ] Message codes (IEFBR14, IGYPS2113-E) are intentionally left visible
- [ ] Tests cover masking for each sensitive category
- [ ] A test asserts secrets do not reach the model prompt

## Webhook dry-run

- [ ] Webhook notify defaults to `dry_run: true`
- [ ] Dry-run mode never sends a network request
- [ ] Real sends (`dry_run: false`) are blocked in READ_ONLY safety mode
- [ ] Notify payloads never include secrets (token/password/api_key stripped)
- [ ] Tests assert dry-run does not send and default is dry-run

## Read-only safety mode

- [ ] READ_ONLY blocks SUBMIT_JCL
- [ ] READ_ONLY blocks real webhook sends (DEVOPS_NOTIFY_SENT)
- [ ] READ_ONLY allows AI_EXPLAIN_SPOOL and DEVOPS_*_SUMMARY (read/analyze)
- [ ] Tests cover each allowed/blocked combination

## Examples

- [ ] examples/config/ownership-rules.example.yaml uses example.org only
- [ ] examples/jenkins and examples/github-actions use fake URLs/secrets
- [ ] examples/api/*.sh use fake values and safe defaults
- [ ] No examples require real IBM Z, Ollama, or webhook access

## Tests

- [ ] Service tests pass (`test_masking`, `test_prompts`,
      `test_ollama_service`, `test_devops`)
- [ ] Django tests pass (`python manage.py test`)
- [ ] Ollama/IBM Z/webhooks are mocked — no real runtime required
- [ ] Tests assert audit log creation on success and error paths
- [ ] Tests assert raw spool not stored in audit logs

## Documentation

- [ ] SECURITY.md present and referenced
- [ ] docs/ai-safety.md present and referenced
- [ ] docs/security-model.md present and referenced
- [ ] docs/security-review-checklist.md present (this file)
- [ ] README reminds users not to commit secrets
- [ ] No production-readiness or Open Mainframe acceptance claims added