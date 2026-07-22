# Good First Issues

> z-agent does not replace Zowe. It builds on Zowe/zOSMF.

This page lists beginner-friendly issue ideas for new contributors. Each item
includes a description, why it helps, suggested files, and a difficulty.

Pick one, open a GitHub Issue to claim it, and follow `CONTRIBUTING.md`. Do
not commit secrets (see `SECURITY.md`).

## 1. Improve demo screenshots

- **Description**: Replace/augment existing screenshots in `screenshots/` and
  link them from the README so the demo flow is self-explanatory.
- **Why it helps**: Reviewers and testers often judge a project by its README
  screenshots first.
- **Suggested files**: `screenshots/`, `README.md`, `docs/demo-script.md`
- **Difficulty**: beginner

## 2. Add more sample spool outputs

- **Description**: Add a few more fake, masked sample spool text files (JCL
  error, ABEND, COBOL compile failure, success) for tests and demos.
- **Why it helps**: Tests and demos become reproducible without real spool.
- **Suggested files**: `examples/samples/`, `test_ollama_service.py`,
  `docs/demo-script.md`
- **Difficulty**: beginner

## 3. Improve README quickstart

- **Description**: Tighten the "Quick Start with Docker" section so a new
  reviewer can go from clone to jobs dashboard in the fewest steps.
- **Why it helps**: First impressions for Open Mainframe reviewers.
- **Suggested files**: `README.md`, `docs/setup.md`
- **Difficulty**: beginner

## 4. Add JSON schema for job summary response

- **Description**: Document the exact JSON schema for
  `POST /api/devops/job-summary` (fields, types, allowed values) so pipelines
  can validate responses.
- **Why it helps**: Makes the DevOps API contract explicit and testable.
- **Suggested files**: `docs/devops-integration.md`, `examples/schemas/`
- **Difficulty**: intermediate

## 5. Add more masking test cases

- **Description**: Add edge-case masking tests (mixed secrets, multiline
  assignments, unusual dataset name formats) to `test_masking.py`.
- **Why it helps**: Masking is a critical safety control; more coverage = more
  confidence.
- **Suggested files**: `test_masking.py`, `agent/masking.py`
- **Difficulty**: beginner

## 6. Improve ownership rules examples

- **Description**: Add more example patterns (wildcards, multi-team) and
  document the matching precedence clearly.
- **Why it helps**: Incident routing becomes easier to configure.
- **Suggested files**: `examples/config/ownership-rules.example.yaml`,
  `docs/incident-routing.md`
- **Difficulty**: beginner

## 7. Add GitLab CI example

- **Description**: Add a `.gitlab-ci.yml` example that calls the z-agent
  job-summary API and gates on `safe_to_continue`.
- **Why it helps**: Broadens DevOps coverage beyond Jenkins/GitHub Actions.
- **Suggested files**: `examples/gitlab-ci/z-agent-mainframe-job-check.yml`,
  `docs/pipeline-examples.md`
- **Difficulty**: intermediate

## 8. Add Azure DevOps pipeline example

- **Description**: Add an Azure DevOps YAML pipeline example for the
  job-summary endpoint.
- **Why it helps**: Reaches Azure DevOps users in hybrid mainframe shops.
- **Suggested files**: `examples/azure-devops/z-agent-job-check.yml`,
  `docs/pipeline-examples.md`
- **Difficulty**: intermediate

## 9. Improve UI copy for AI explanation

- **Description**: Clarify the wording in the spool viewer's AI explanation
  panel (advisory-only disclaimer, field labels).
- **Why it helps**: Reduces the risk users treat AI output as authoritative.
- **Suggested files**: `jobfrontend/jobs/templates/jobs/job_spool.html`,
  `docs/ai-safety.md`
- **Difficulty**: beginner

## 10. Add FAQ section

- **Description**: `docs/faq.md` already exists (v0.6.0). Add more
  reviewer/adopter questions and cross-link from the README.
- **Why it helps**: Reduces repeated questions during community review.
- **Suggested files**: `docs/faq.md`, `README.md`
- **Difficulty**: beginner

## 11. Add a JSON schema for incident summary response

- **Description**: Document the JSON schema for
  `POST /api/devops/incident-summary` (title, severity, summary, evidence,
  recommended_owner, suggested_next_step, audit_id).
- **Why it helps**: Lets incident tools validate z-agent output.
- **Suggested files**: `docs/devops-integration.md`, `examples/schemas/`
- **Difficulty**: intermediate

## 12. Add a dry-run notify payload schema

- **Description**: Document the payload shape returned by
  `POST /api/devops/notify` in dry-run mode.
- **Why it helps**: Pipelines and webhook targets know what to expect.
- **Suggested files**: `docs/devops-integration.md`, `examples/schemas/`
- **Difficulty**: beginner

## 13. Add more spool diagnosis patterns

- **Description**: Extend `diagnose_spool` in `main.py` with more rule-based
  patterns (e.g. IEW link-edit errors, specific ABEND codes) + tests.
- **Why it helps**: Better rule-based diagnosis improves AI explanations and
  job summaries.
- **Suggested files**: `main.py`, `test_ollama_service.py`, `docs/ai-operations.md`
- **Difficulty**: intermediate

## 14. Add a CI workflow to run tests on PRs

- **Description**: Add a GitHub Actions workflow that runs
  `python -m unittest test_masking test_prompts test_ollama_service test_devops`
  and `python manage.py test` on every PR.
- **Why it helps**: Keeps the repo green and signals quality to reviewers.
- **Suggested files**: `.github/workflows/tests.yml`
- **Difficulty**: intermediate

## 15. Improve docs navigation

- **Description**: Add a `docs/INDEX.md` or a table of contents that groups
  docs by audience (reviewer / tester / contributor / operator).
- **Why it helps**: Big doc set is hard to navigate; a map helps reviewers.
- **Suggested files**: `docs/INDEX.md`, `README.md`
- **Difficulty**: beginner