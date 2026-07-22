# Incident Routing

> Do not use production IBM Z credentials, real spool output, private SMF
> data, or company-sensitive data in public examples or issues.

z-agent can map a failed job to a recommended owner so incident summaries are
easier to route in ServiceNow, Jira, Slack, or Teams.

## Ownership rules file

See `examples/config/ownership-rules.example.yaml` for a safe, fake-data
example:

```yaml
ownership_rules:
  - job_pattern: "PAY*"
    team: "Payroll Team"
    notify:
      email: "payroll-ops@example.org"
      webhook: "https://example.org/webhook/payroll"

  - job_pattern: "BILL*"
    team: "Billing Team"
    notify:
      email: "billing-ops@example.org"

  - job_pattern: "DEV*"
    team: "Development Team"
    notify:
      email: "dev-mainframe@example.org"
```

## How matching works

- z-agent matches `job_name` against `job_pattern` using `fnmatch` wildcards
  (`"PAY*"` matches `"PAYROLL01"`).
- Matching is case-insensitive.
- The **first** matching rule wins.
- If no rule matches, the recommended owner is:
  `Unknown - configure ownership rules`

## Where to configure the rules

Two ways:

1. **Default path**: place the rules at
   `examples/config/ownership-rules.example.yaml` (already gitignored-safe
   only as an example; copy it to a private location for real use).
2. **Override per request**: send the `X-Ownership-Rules-Path` header pointing
   to your own rules file on the z-agent server.

You can also set the environment variable `OWNERSHIP_RULES_PATH` on the z-agent
backend to point at your private rules file at startup.

## How it surfaces in APIs

- `POST /api/devops/incident-summary` returns `recommended_owner` and
  `suggested_next_step`.
- `POST /api/devops/notify` can include ownership metadata in the payload so a
  webhook can route to the right channel.

## Safety notes

- The committed example uses only fake emails and fake webhook URLs.
- Never put real company emails, private hostnames, or real webhook URLs in the
  committed example. Use a private copy referenced by `OWNERSHIP_RULES_PATH`
  or the `X-Ownership-Rules-Path` header.
- Ownership routing is deliberately simple (pattern → team/notify). Complex
  enterprise routing (severity-based escalation, on-call schedules, time
  windows) is future work.

## Limitations

- Only `job_pattern` → `team`/`notify` is supported today.
- No on-call schedule or time-window routing.
- No automatic webhook fan-out from ownership rules in the current preview
  (use `POST /api/devops/notify` explicitly, in dry-run by default).