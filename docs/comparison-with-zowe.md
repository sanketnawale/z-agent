# Comparison with Zowe

> z-agent does not replace Zowe. Zowe provides access and framework; z-agent
> provides AI-assisted operations workflows, safety modes, audit logs, and a
> Django UI/API experience on top.

This comparison is written with respect for the Zowe project. Zowe is a
foundational Open Mainframe Project effort and z-agent depends on it. The goal
here is to clarify where each tool fits, not to rank them.

## At a glance

| Tool | Primary role | Provided by | z-agent relationship |
| --- | --- | --- | --- |
| Zowe CLI | z/OS access via commands | Zowe | **Hard dependency** — z-agent calls Zowe CLI |
| Zowe Explorer | VS Code dataset/job/USS browsing | Zowe | Complementary IDE experience |
| Zowe Desktop | Web/desktop app framework (ZLux) | Zowe | Different framework; z-agent uses Django |
| Zowe MCP Server | Model Context Protocol tool access | Zowe | Future integration target |
| z-agent | AI-assisted operations layer | Independent | Builds on Zowe/zOSMF |

## Zowe CLI

Zowe CLI is the command-line interface to z/OSMF. It lets you list jobs, view
spool, browse datasets, submit JCL, and manage USS files from a terminal or
scripts.

- **Provided by**: Zowe.
- **Best at**: direct, scriptable z/OS access; CI/CD automation; the access
  foundation for other tools.
- **z-agent relationship**: z-agent uses Zowe CLI as its access layer. Every
  jobs/spool/dataset/USS operation in z-agent goes through Zowe CLI under the
  hood. z-agent does not reimplement z/OS access — it relies on Zowe for that.

## Zowe Explorer

Zowe Explorer is a VS Code extension that brings dataset, job, and USS browsing
into the editor. It is ideal for developers working inside VS Code.

- **Provided by**: Zowe.
- **Best at**: in-editor mainframe workflows for developers who already live in
  VS Code.
- **z-agent relationship**: complementary. Zowe Explorer is an IDE experience;
  z-agent is a standalone browser-based UI/API with AI-assisted spool
  explanation, safety modes, and audit logging. They can coexist and share the
  same Zowe profiles and z/OSMF backends.

## Zowe Desktop

Zowe Desktop (Zowe Application Framework / ZLux) is a web/desktop application
framework for building mainframe apps. It is a framework, not a specific
operations product.

- **Provided by**: Zowe.
- **Best at**: hosting extensible mainframe web apps inside the Zowe framework.
- **z-agent relationship**: different layer. z-agent is a focused application
  built with Django/FastAPI, not a Zowe Desktop applet. z-agent could in the
  future be packaged as a Zowe Desktop app if there is community interest, but
  today it stands as an independent operations UI that calls Zowe CLI.

## Zowe MCP Server

The Zowe MCP (Model Context Protocol) server exposes Zowe capabilities to
MCP-compatible AI clients, so models can call mainframe operations as tools.

- **Provided by**: Zowe.
- **Best at**: giving AI assistants structured access to z/OS operations as
  tools, within an MCP-capable client.
- **z-agent relationship**: future integration target. z-agent currently calls
  Zowe CLI directly and runs its own Ollama-based explanation with masking and
  audit logging. As Zowe MCP matures, z-agent could consume MCP tools as one
  access option while keeping its safety, masking, and audit layer in place.

## z-agent

z-agent is an AI-assisted IBM Z operations platform. It does not provide z/OS
access itself — it builds on Zowe/zOSMF for access and adds an operations
experience on top.

- **Provided by**: independent open-source project (Apache-2.0).
- **Best at**:
  - turning spool output into structured, masked, audited AI explanations
  - safety-gated JCL submission
  - a browser UI and REST API for hybrid teams that do not live in a terminal
- **What it adds on top of Zowe/zOSMF**:
  - evidence-based Python spool diagnosis
  - sensitive-data masking before AI analysis
  - structured AI explanation (likely cause, evidence, next step, confidence,
    audit ID)
  - safety modes and approval flow
  - audit logging for read and write actions
  - dataset/USS browsing and member explanation

## How to think about them together

- **Zowe** = access and framework (CLI, Explorer, Desktop, MCP).
- **z-agent** = an AI-assisted, safe, auditable operations layer that *uses*
  Zowe for access.

A typical setup: install Zowe CLI, configure z/OSMF, then run z-agent to get a
guided, audited, AI-assisted operations experience for the same system. z-agent
never asks teams to choose between the two — it is designed to sit on top of
Zowe.

See `docs/landscape.md` for a broader ecosystem comparison and
`docs/open-mainframe-alignment.md` for the project's positioning.