# Governance

This document describes how z-agent is governed today and how we intend it to
grow.

## Current model

z-agent is a **maintainer-led** project. Today there is a single maintainer who
is responsible for project direction, releases, and final review of changes.

See `MAINTAINERS.md` for the active maintainers and their areas.

## Decision making

- **Issues and PRs are discussed publicly** on GitHub.
- **Maintainers review all changes** before merge. No change is merged without
  maintainer review.
- **Security issues** follow `SECURITY.md` and are reported privately, not via
  public issues with sensitive details.
- **Major changes** (new features, safety/audit behavior changes, breaking API
  changes) should start as a **GitHub Issue** to be discussed before a PR is
  opened.
- Small fixes, docs, and tests can go straight to a focused PR.

## Branching and releases

- Feature work happens on `feat/*` branches, not directly on `main`.
- PRs are opened against `main` and reviewed before merge.
- Releases are tagged and recorded in `CHANGELOG.md`.

## Principles (non-negotiable)

- z-agent does not replace Zowe; it builds on Zowe/zOSMF.
- No secrets or sensitive mainframe data are committed to the repository.
- Safety modes and audit logging must not be weakened without public
  discussion.
- AI explanations remain advisory only and must never execute actions on IBM Z.

## Governance growth path

z-agent is intentionally small today. As adoption grows, the goal is to:

1. Add maintainers for additional areas (see `MAINTAINERS.md`).
2. Move from maintainer-led to a small maintainer council with documented
   ownership.
3. Adopt contributor ladders (contributor → reviewer → maintainer) with clear
   expectations.
4. Formalize release and security processes.

Until then, the current maintainer owns final decisions and is the point of
contact for `SECURITY.md` reports.

See `CONTRIBUTING.md` for how to contribute and `TESTERS.md` for how to give
early feedback.