# Maintainers

This file lists the active maintainers of z-agent and the areas they own.
It is intentionally small today and will grow as the project adopts more
contributor oversight (see `GOVERNANCE.md`).

## Maintainers

| Name | GitHub | Areas |
| --- | --- | --- |
| Sanket Nawale | [@sanketnawale](https://github.com/sanketnawale) | Project direction, IBM Z/Zowe integration, Django UI/API, safety/audit/docs |

## Areas of ownership

- **Project direction**: roadmap, milestones, release sequencing, community
  positioning.
- **IBM Z / Zowe integration**: Zowe CLI usage, z/OSMF interactions, jobs/spool/
  dataset/USS/JCL workflows.
- **Django UI / API**: frontend views, templates, REST proxy endpoints,
  session handling.
- **Safety / audit / docs**: safety modes, audit logging, AI masking, prompt
  safety, project documentation and governance files.

## Review expectations

Maintainers are expected to:

- review PRs in their areas
- ensure no secrets or sensitive mainframe data are committed
- preserve the safety and audit model
- keep z-agent strictly complementary to Zowe

## Adding maintainers

New maintainers are added by public proposal via a GitHub Issue, followed by
maintainer agreement. Contributor ladders and a council model are a future goal
described in `GOVERNANCE.md`.