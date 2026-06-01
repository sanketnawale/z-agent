# Z-Agent Demo Checklist

Use this checklist before and during a live demo of Z-Agent.

---

## Before the Demo

### 1. Start Docker

```bash
cd /mnt/c/Users/sanke/Documents/IBM-III/IBM-III/new
docker compose up -d
```

Check running containers:

```bash
docker ps
```

Expected output includes:

```
z-agent
z-agent-ollama
```

---

### 2. Check Ollama Model

```bash
curl http://127.0.0.1:11434/api/tags
```

Expected: `llama3.2:3b` is listed.

If missing:

```bash
docker exec -it z-agent-ollama ollama pull llama3.2:3b
```

---

### 3. Verify FastAPI Health

```bash
curl http://127.0.0.1:3001/health
```

Expected:

```json
{"status": "ok"}
```

---

### 4. Open Z-Agent

Open in browser:

```
http://127.0.0.1:8001
```

Expected: redirected to `/setup/`

---

## During the Demo

### 5. Login

Enter IBM Z / z/OSMF credentials:

| Field | Value |
|---|---|
| Host | `204.90.115.200` |
| Port | `10443` |
| User ID | `Z00805` |
| Password | `your-password` |
| Allow self-signed certificate | ✓ checked |

AI settings for Docker demo:

```
Provider:    Server Ollama
Model:       llama3.2:3b
Ollama URL:  http://ollama:11434/api/generate
```

---

### 6. Jobs Dashboard

Open: `http://127.0.0.1:8001/jobs/`

Show:

- Job list with return codes
- Severity colour badges (success / warning / error)
- Link to open spool

---

### 7. Spool Diagnosis

Open a failed job spool. Show:

| Field | Description |
|---|---|
| Final result | One-line outcome |
| Return code | e.g. `RC 0008` |
| Root cause | Why it failed |
| Impact | What was skipped |
| Recommended fix | What to do next |
| Evidence | Real spool lines |

Good demo jobs:

- JCL validation failed
- COBOL compile failed (`IGYPS2113-E`)
- Job completed successfully (RC 0000)

---

### 8. AI Explanation

Click **Explain Spool**.

Show AI explanation panel. Say verbally:

> "Z-Agent first extracts a deterministic diagnosis from the spool.
> Then the AI only explains that diagnosis in plain English.
> The AI cannot invent errors that are not in the spool."

---

### 9. Dataset Explorer

Open: `http://127.0.0.1:8001/explorer/`

Show:

- Dataset search by pattern
- Member list for a PDS
- Member content preview (JCL or COBOL)
- Optional: submit JCL from member

---

### 10. USS Browser

Open: `http://127.0.0.1:8001/uss/`

Show:

- Dynamic USS home detection
- Folder navigation
- File permissions and owner
- File content preview

Example home path:

```
/z/z00805
```

---

### 11. AI Settings

Open: `http://127.0.0.1:8001/ai-settings/`

Show available providers:

- Rule-based only
- Server Ollama
- Custom / Local Ollama URL
- Gemini API
- Claude API
- OpenAI API

Say verbally:

> "Users can switch providers without restarting the server.
> Each session stores its own selected provider.
> Logout clears the session completely."

---

### 12. Logout

Click **Logout**.

Expected: redirected to `/setup/`

Confirm: opening `/jobs/` again redirects back to setup.

---

## After the Demo / Backup Commands

```bash
# View Z-Agent logs
docker logs -f z-agent

# View Ollama logs
docker logs -f z-agent-ollama

# Restart all containers
docker compose restart

# Rebuild Z-Agent after code changes
docker compose up -d --build z-agent

# Stop everything
docker compose down
```

---

## Conference Pitch (one sentence)

> Z-Agent is a lightweight, safety-first MainframeOps learning assistant that helps students and junior developers submit JCL, monitor jobs, inspect spool output, browse datasets and USS files, and understand failures using pluggable AI providers.

---

## Future Goals to Mention

- Full job lifecycle automation: submit → monitor → diagnose → explain
- Safety approval layer for automated actions
- Audit log
- Multi-user hosted mode
- Guided JCL and COBOL fix suggestions
- Classroom mode for educators
