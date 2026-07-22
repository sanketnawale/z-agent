# Release Checklist

> z-agent does not replace Zowe. It builds on Zowe/zOSMF.

Use this checklist before tagging a z-agent release. It is written for the
maintainer and assumes a local clone on Windows or Linux.

## Before release

- [ ] All tests pass (see commands below)
- [ ] Diff scanned for secrets (no `.env`, `zowe.config.json`, tokens, certs)
- [ ] CHANGELOG updated for the new version
- [ ] README updated if user-facing behavior changed
- [ ] Documentation links verified (README/docs links point to existing files)
- [ ] `.env`, `zowe.config.json`, `db.sqlite3`, `*.sqlite3` confirmed ignored
- [ ] No raw spool / SMF / private hostnames committed
- [ ] Screenshots or demo notes updated if UI changed
- [ ] Branch is clean and pushed
- [ ] Tag created
- [ ] GitHub release created
- [ ] Release notes reference CHANGELOG entry

## Run tests

Run the service-level tests (from the repo root):

```bash
python -m unittest test_masking test_prompts test_ollama_service test_devops
```

Run the Django tests (from `jobfrontend/`):

```bash
python manage.py test
```

Both suites must pass before tagging.

## Scan diff for secrets

Before tagging, review the diff between the last release tag and HEAD:

```bash
git log --oneline v0.5.0..HEAD
git diff v0.5.0..HEAD --name-only
```

Then scan content for suspicious tokens/credentials (use any of: grep/rg,
your editor, or the examples-no-secrets test). Expected: only fake/example.org
values.

## Verify ignored files are not tracked

```bash
git check-ignore -v .env zowe.config.json db.sqlite3 zowe.schema.json
git ls-files | grep -E "\.env$|zowe\.config|\.sqlite3"
```

The second command should print nothing.

## Tag and release

```bash
git status
python -m unittest test_masking test_prompts test_ollama_service test_devops
python manage.py test
git tag v0.6.0-sandbox-candidate
git push origin v0.6.0-sandbox-candidate
```

Then create the GitHub release from the tag, referencing the CHANGELOG entry.
Upload screenshots or demo notes if applicable.

## After release

- [ ] Confirm the GitHub release is published
- [ ] Post release link in project communication channels
- [ ] Update ROADMAP if milestones shifted
- [ ] Open issues for any follow-ups discovered during the release