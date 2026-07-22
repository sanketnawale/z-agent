# Landscape

> An open-source, local-first, Zowe-based IBM Z operations platform with Django
> UI/API, Ollama/local AI, safety modes, audit logging, job/spool/JCL
> workflows, dataset/USS views, and future DevOps/Kubernetes/SMF integration.

This document places z-agent in the IBM Z tooling landscape. It is intended to
be honest and ecosystem-aligned, not promotional. Each tool below has real value
and z-agent does not claim to replace any of them.

## The gap z-agent addresses

Today the IBM Z ecosystem has excellent **access** tooling (Zowe), excellent
**IDE** experiences (Zowe Explorer, IBM watsonx Code Assistant for Z), and
excellent **enterprise** AIOps platforms. What is missing is an **open-source,
local-first operations layer**: a project that uses Zowe for access and adds a
web UI/API, local AI explanations, safety modes, and audit logging for the
day-to-day job/spool/JCL operations loop — without sending raw sensitive spool
to the cloud and without requiring an enterprise AIOps license.

z-agent aims to fill that gap.

## Tool-by-tool comparison

### Zowe

- **What it is**: Open Mainframe Project framework and CLI for z/OS access via
  z/OSMF.
- **Strengths**: standard, scriptable, extensible, broad community.
- **z-agent relationship**: z-agent depends on Zowe CLI for all z/OS access.
  z-agent adds an operations layer on top; it does not duplicate Zowe.

### Zowe MCP Server

- **What it is**: exposes Zowe capabilities as Model Context Protocol tools for
  AI clients.
- **Strengths**: lets MCP-compatible assistants call mainframe operations
  natively as tools.
- **z-agent relationship**: complementary. z-agent runs its own masking +
  audit + Ollama explanation today; Zowe MCP could become an optional access
  option in the future, with z-agent's safety/audit layer remaining in control.

### Zowe Desktop

- **What it is**: a web/desktop application framework for mainframe apps.
- **Strengths**: extensible host for mainframe web apps within the Zowe
  ecosystem.
- **z-agent relationship**: different layer. z-agent is a focused Django/FastAPI
  application, not a Zowe Desktop applet, but could be packaged as one later.

### Zowe Explorer

- **What it is**: VS Code extension for dataset/job/USS browsing.
- **Strengths**: great in-editor developer experience for VS Code users.
- **z-agent relationship**: complementary IDE tooling. z-agent provides a
  standalone browser UI/API with AI explanation and audit logging for hybrid
  teams who want a web experience.

### IBM watsonx Assistant for Z

- **What it is**: IBM's conversational/assistant offering for Z.
- **Strengths**: enterprise-grade, IBM-supported, deep integrations.
- **z-agent relationship**: watsonx Assistant targets assisted/knowledge
  workflows within IBM's ecosystem and is typically cloud/enterprise. z-agent is
  open-source and local-first (Ollama), focused on the operations loop
  (jobs/spool/JCL) with explicit safety modes and audit logging. They address
  different audiences; z-agent is for teams who want a transparent, auditable,
  self-hostable option.

### IBM watsonx Code Assistant for Z

- **What it is**: AI assistant focused on Z application modernization and code
  (COBOL/PL/I).
- **Strengths**: code generation, refactoring, and modernization guidance,
  IBM-supported.
- **z-agent relationship**: different focus. watsonx Code Assistant helps you
  *write and modernize code*; z-agent helps you *operate and triage jobs* —
  explaining spool/JCL failures, masking sensitive data, and logging actions.
  They are complementary, not overlapping.

### IBM SMF Explorer

- **What it is**: tooling for exploring SMF (System Management Facility)
  records.
- **Strengths**: performance/capacity/audit analytics on SMF data.
- **z-agent relationship**: SMF analytics is an explicit future direction for
  z-agent (behind authorized access and a safety model). z-agent today focuses
  on job/spool/JCL/dataset/USS operations. SMF Explorer and z-agent could
  eventually serve complementary telemetry vs. operations use cases.

### Galasa

- **What it is**: Open Mainframe Project integration testing framework for
  mainframe applications.
- **Strengths**: automated, repeatable testing across z/OS and distributed
  systems.
- **z-agent relationship**: different problem domain. Galasa is about *testing*
  mainframe applications; z-agent is about *operating and triaging* mainframe
  jobs. They do not overlap functionally but serve the same ecosystem goal of
  modernizing mainframe engineering.

### Enterprise AIOps tools

- **What they are**: commercial platforms for incident detection, correlation,
  and automated remediation across hybrid infrastructure.
- **Strengths**: scale, enterprise integrations, ML-driven alerting, vendor
  support.
- **z-agent relationship**: enterprise AIOps platforms are broad, licensed, and
  often cloud-mediated. z-agent is narrow, open-source, local-first, and
  focused on the IBM Z operations loop with transparent safety/audit. z-agent is
  a good fit for teams who cannot or do not want to feed raw mainframe data into
  a commercial platform, and who want a foundation they can inspect and extend.

## Where z-agent sits

```
                Access / framework          IDE / assistant            Operations layer
                -----------------          -----------------          ------------------
Open source     Zowe CLI, Zowe             Zowe Explorer               z-agent
                Desktop, Zowe MCP          (VS Code)                   (Django UI/API, local AI,
                                                                        safety, audit)

IBM / proprietary                          watsonx Code Assistant      Enterprise AIOps
                                            for Z                      watsonx Assistant for Z
```

z-agent occupies the **open-source / operations** cell, building on Zowe for
access, complementing Zowe Explorer for IDE workflows, and staying clearly
separate from IBM's proprietary assistant/AIOps offerings.

## Why open-source and local-first matters here

Mainframe spool, dataset, and SMF data are sensitive. An open-source project that
runs locally and defaults to a local model lets teams:

- inspect exactly what is sent to the model (masking is in the code)
- avoid sending raw spool to the cloud
- keep an auditable, reviewable operations trail
- extend the workflow to their own environments without a vendor lock-in

That is the gap z-agent is built to close. See `docs/open-mainframe-alignment.md`
for the project's positioning and `docs/use-cases.md` for concrete scenarios.