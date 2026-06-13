# Z-Agent Demo Guide

This guide explains how to run and demonstrate Z-Agent.

## 1. Start Z-Agent with Docker

From the project root:

    docker compose up -d --build

Check containers:

    docker ps

Expected containers:

- z-agent
- z-agent-ollama

## 2. Pull Ollama Model

If using local/server Ollama:

    docker exec -it z-agent-ollama ollama pull llama3.2:3b

Check Ollama models:

    docker exec -it z-agent-ollama ollama list

## 3. Open the Web App

Open:

    http://localhost:8001

For server deployment:

    http://SERVER_IP:8001

## 4. Setup IBM Z Connection

On the setup page, enter:

- z/OSMF host
- z/OSMF port
- IBM Z user ID
- IBM Z password
- Certificate option
- AI provider
- AI model

For Docker Ollama mode, use:

    http://ollama:11434/api/generate

## 5. Demo Flow

Recommended live demo flow:

1. Open setup page
2. Enter IBM Z connection details
3. Open Jobs dashboard
4. Select a job
5. Open spool output
6. Show rule-based diagnosis
7. Click AI explanation
8. Open Dataset Explorer
9. Open USS Browser
10. Open AI Settings and show model switching
11. Logout

## 6. What to Explain

Main message:

    Zowe gives access. Z-Agent adds guidance.

Architecture:

    Browser -> Django -> FastAPI -> Zowe CLI -> z/OSMF -> IBM Z

AI flow:

    Spool output -> Python diagnosis -> AI Gateway -> selected model -> explanation

## 7. Demo Safety

Do not show:

- Real passwords
- API keys
- Private certificates
- Sensitive production spool output
- Company/private IBM Z data

Use demo accounts and sample data whenever possible.

## 8. Current Limitations

Z-Agent is currently an MVP and demo-oriented project.

Known limitations:

- Not production-ready without security review
- No role-based access control yet
- No full audit log yet
- JCL submit safety approval is planned
- SMF analytics is future work and requires authorized data access
