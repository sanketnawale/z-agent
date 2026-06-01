# Z-Agent

**Z-Agent** is a lightweight MainframeOps learning assistant for IBM Z students, junior developers, and educators.

It connects to IBM Z through Zowe CLI and provides a modern browser interface for:

- IBM Z / z/OSMF session login
- Job listing and severity classification
- Spool viewing and parsing
- Rule-based job diagnosis
- AI-assisted spool explanation
- Dataset browsing and member viewing
- JCL submission from the browser
- USS file browsing and preview
- Pluggable AI providers (Ollama, Gemini, Claude, OpenAI)
- Docker-based local deployment

> Z-Agent is not designed to replace enterprise IBM Z tooling.  
> It is designed to make mainframe learning more visual, guided, and accessible using tools students can actually use.

---

## Architecture

```
Browser
  ↓
Django frontend (port 8001)
  ↓
FastAPI backend (port 3001)
  ↓
Zowe CLI → IBM Z / z/OSMF
Ollama / Cloud AI APIs
```

---

## Current Features

### Jobs and Spool

- List submitted jobs
- Open full job spool output
- Extract important evidence lines automatically
- Detect common job outcomes using rule-based diagnosis
- Explain return codes, JCL failures, COBOL compile failures, and successful jobs in plain English

Supported diagnosis cases:

| Pattern | Detection |
|---|---|
| `$HASP395 ... RC=0000` | Job completed successfully |
| `IGYPS2113-E` | COBOL compile failed |
| `JCL ERROR` / `IEFC...` | JCL validation failed |
| `ABEND` | Runtime failure |
| Non-zero RC | Warning / error |

---

### Dataset Explorer

- Search datasets by pattern
- List members inside a PDS/PDSE
- Preview member content (JCL, COBOL, REXX)
- Submit JCL directly from a selected member

---

### USS Browser

- Detect dynamic USS home path from the logged-in user ID
- Browse USS folders and navigate into subdirectories
- Preview readable USS files
- Show permissions and owner for each entry

For IBM Z Xplore users, the USS home is typically:

```
/z/<userid-lowercase>

Example:
  User:     Z00805
  USS Home: /z/z00805
```

---

### AI Provider Layer

Z-Agent supports selectable AI providers per session:

| Provider | Mode |
|---|---|
| Rule-based only | No AI, deterministic diagnosis only |
| Server Ollama | Ollama running inside Docker |
| Custom / Local Ollama URL | Ollama running on host machine |
| Gemini API | Google Gemini (requires API key) |
| Claude API | Anthropic Claude (requires API key) |
| OpenAI API | OpenAI (requires API key) |

**Design principle:**

```
Raw spool
  → Z-Agent rule-based diagnosis (deterministic)
    → AI explains the diagnosis in simple English
```

AI does not replace the diagnosis. AI only explains the extracted evidence.

---

## Docker Architecture

Z-Agent runs with two containers:

| Container | Role |
|---|---|
| `z-agent` | Django frontend + FastAPI backend + Zowe CLI |
| `z-agent-ollama` | Ollama model server |

Docker Compose starts both services together.

---

## Requirements

- Docker Desktop or Docker Engine
- Docker Compose
- Internet access (for pulling images and models)
- IBM Z / z/OSMF credentials
- Optional: Gemini, Claude, or OpenAI API key
- Optional: Ollama local model

---

## Quick Start with Docker

From the project root:

```bash
docker compose build
docker compose up -d
```

Check running containers:

```bash
docker ps
```

Expected:

```
z-agent
z-agent-ollama
```

Pull the Ollama model:

```bash
docker exec -it z-agent-ollama ollama pull llama3.2:3b
```

Verify Ollama:

```bash
curl http://127.0.0.1:11434/api/tags
```

Open Z-Agent:

```
http://127.0.0.1:8001
```

---

## Login Setup

On the setup page, enter your IBM Z credentials:

| Field | Example |
|---|---|
| Host | `204.90.115.200` |
| Port | `10443` |
| User ID | `Z00805` |
| Password | `your-password` |
| Allow self-signed certificate | ✓ checked (for Xplore/lab systems) |

---

## AI Setup

### Docker Ollama (recommended for demos)

```
Provider:    Server Ollama
Model:       llama3.2:3b
Ollama URL:  http://ollama:11434/api/generate
```

### Local Ollama (non-Docker)

```
Provider:    Custom / Local Ollama URL
Model:       llama3.2:3b
Ollama URL:  http://127.0.0.1:11434/api/generate
```

### Gemini API

```
Provider:    Gemini API
Model:       gemini-2.5-flash
API Key:     your Gemini API key
```

### Claude API

```
Provider:    Claude API
Model:       claude-3-5-haiku-latest
API Key:     your Anthropic API key
```

### OpenAI API

```
Provider:    OpenAI API
Model:       gpt-4.1-mini
API Key:     your OpenAI API key
```

---

## Useful Docker Commands

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Rebuild Z-Agent after code changes
docker compose up -d --build z-agent

# View Z-Agent logs
docker logs -f z-agent

# View Ollama logs
docker logs -f z-agent-ollama

# Enter Z-Agent container
docker exec -it z-agent bash

# Enter Ollama container
docker exec -it z-agent-ollama bash

# Test FastAPI inside Z-Agent container
curl http://127.0.0.1:3001/health

# Test Ollama from inside Z-Agent container
curl http://ollama:11434/api/tags
```

---

## Local Development Mode

### Start FastAPI

```bash
cd /mnt/c/Users/sanke/Documents/IBM-III/IBM-III/new
source venv_linux/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 3001 --reload
```

### Start Django

```bash
cd /mnt/c/Users/sanke/Documents/IBM-III/IBM-III/new/jobfrontend
source ../venv_linux/bin/activate
python manage.py runserver 0.0.0.0:8001
```

Open:

```
http://127.0.0.1:8001
```

---

## Demo Flow

1. Open Z-Agent at `http://127.0.0.1:8001`
2. Enter IBM Z credentials on the setup page
3. Select AI provider
4. Open **Jobs** — see job list with severity badges
5. Open a failed job spool
6. Show rule-based diagnosis (headline, root cause, impact, fix, evidence)
7. Click **Explain Spool** — show AI explanation
8. Open **Dataset Explorer** — browse datasets and members
9. Open a JCL or COBOL member — show content preview
10. Open **USS Browser** — show dynamic home, folders, and file preview
11. Click **Logout** — confirm session is cleared

---

## Roadmap

### Near Term

- Dockerized deployment (in progress)
- Better UI polish
- Stronger spool evidence extraction
- More diagnosis patterns
- Demo-ready documentation

### Mid Term

- Full job lifecycle automation:
  - Submit JCL
  - Capture Job ID
  - Monitor status
  - Read spool
  - Diagnose result
  - Explain outcome
- Audit log
- Safety approval layer
- Multi-user hosted deployment

### Long Term

- Agentic MainframeOps workflows
- Guided JCL and COBOL fix suggestions
- IDE extension integration
- Classroom mode for educators
- Enterprise policy and access-control layer

---

## Project Positioning

> Z-Agent is a lightweight, safety-first MainframeOps learning assistant that helps students and junior developers submit JCL, monitor jobs, inspect spool output, browse datasets and USS files, and understand failures using pluggable AI providers.

It is not just a spool analyzer. It is a **guided IBM Z learning and operations assistant**.

---

## Presented at

**GSE Nordic 2026 — Helsinki**  
*Z-Agent: Bringing Mainframe Job Insights to Life with Zowe and Python*  
Beginner | Student | IBM Z Infrastructure and Application Development
