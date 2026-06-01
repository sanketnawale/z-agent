import json
import os
import re
import subprocess
from typing import List, Dict, Any
from ai_gateway import explain_with_ai

import requests
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()
app = FastAPI(title="Z-Agent API")

ZOWE_BIN = os.getenv("ZOWE_BIN", "zowe")
ZOWE_HOST = os.getenv("ZOWE_HOST", "204.90.115.200")
ZOWE_PORT = os.getenv("ZOWE_PORT", "10443")
ZOWE_USER = os.getenv("ZOWE_USER", "Z00805")
USS_HOME = os.getenv("USS_HOME", f"/z/{ZOWE_USER.lower()}")
ZOWE_PASSWORD = os.getenv("ZOWE_PASSWORD", "")
ZOWE_REJECT_UNAUTHORIZED = os.getenv("ZOWE_REJECT_UNAUTHORIZED", "false")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
DATASET_FILTER = os.getenv("DATASET_FILTER", f"{ZOWE_USER}.*")


class TextPayload(BaseModel):
    content: str


class SubmitPayload(BaseModel):
    dataset_member: str


def fallback_zowe_config() -> Dict[str, str]:
    return {
        "host": ZOWE_HOST,
        "port": ZOWE_PORT,
        "user": ZOWE_USER,
        "password": ZOWE_PASSWORD,
        "ru": ZOWE_REJECT_UNAUTHORIZED,
    }


def get_zowe_config(request: Request) -> Dict[str, str]:
    """
    Read per-user credentials sent by Django session.
    If no headers are sent, fall back to .env developer mode.
    """
    host = request.headers.get("X-Zowe-Host") or ZOWE_HOST
    port = request.headers.get("X-Zowe-Port") or ZOWE_PORT
    user = request.headers.get("X-Zowe-User") or ZOWE_USER
    password = request.headers.get("X-Zowe-Password") or ZOWE_PASSWORD
    ru = request.headers.get("X-Zowe-RU") or ZOWE_REJECT_UNAUTHORIZED

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "ru": ru,
    }

def get_ai_config(request: Request) -> Dict[str, str]:
    return {
        "provider": request.headers.get("X-AI-Provider", "server_ollama"),
        "model": request.headers.get("X-AI-Model", "llama3.2:3b"),
        "api_key": request.headers.get("X-AI-API-Key", ""),
        "ollama_url": request.headers.get(
            "X-Ollama-URL",
            os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate"),
        ),
    }
def user_uss_home(config: Dict[str, str]) -> str:
    explicit_home = os.getenv("USS_HOME", "").strip()
    if explicit_home:
        return explicit_home

    return f"/z/{config['user'].lower()}"


def run_zowe(args: List[str], config: Dict[str, str] = None) -> str:


    config = config or fallback_zowe_config()

    cmd = [
        ZOWE_BIN,
        *args,
        "--host", config["host"],
        "--port", str(config["port"]),
        "--user", config["user"],
        "--password", config["password"],
        "--ru", config["ru"],
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=result.stderr.strip() or result.stdout.strip() or "Zowe command failed",
        )

    return result.stdout.strip()


def parse_jobs(lines: List[str]) -> List[Dict[str, str]]:
    jobs = []
    for line in lines:
        parts = line.split(maxsplit=4)
        if len(parts) == 5:
            jobs.append({
                "jobid": parts[0],
                "retcode": f"{parts[1]} {parts[2]}",
                "jobname": parts[3],
                "status": parts[4],
            })
    return jobs


def parse_spool_sections(spool_content: str) -> List[Dict[str, Any]]:
    sections = []
    current = None
    for line in spool_content.splitlines():
        if line.startswith("Spool file:"):
            if current:
                sections.append(current)
            current = {"title": line, "content": []}
        elif current:
            current["content"].append(line)
    if current:
        sections.append(current)
    return sections


def extract_message_codes(text: str) -> List[str]:
    found = re.findall(r"\b[A-Z]{3,5}\d{3,5}[A-Z]?\b", text)
    ordered = []
    seen = set()
    for code in found:
        if code not in seen:
            seen.add(code)
            ordered.append(code)
    return ordered[:15]


def simple_diagnosis(text: str) -> Dict[str, Any]:
    upper = text.upper()
    messages = extract_message_codes(upper)
    diagnosis = []
    severity = "info"

    if "CC 0000" in upper:
        diagnosis.append("Job appears to have completed successfully with CC 0000.")
        severity = "success"
    if "JCL ERROR" in upper or "IEFC" in upper:
        diagnosis.append("Detected JCL-related validation or syntax issues before execution.")
        severity = "error"
    if "ABEND" in upper:
        diagnosis.append("Detected ABEND output, which usually indicates a runtime failure.")
        severity = "error"
    if "ACTIVE" in upper and severity != "error":
        diagnosis.append("Job appears active or still in progress.")
        severity = "warning"
    if not diagnosis:
        diagnosis.append("No direct rule-based diagnosis matched; inspect JESMSGLG, JESJCL, and JESYSMSG sections.")

    return {
        "severity": severity,
        "messages": messages,
        "summary": diagnosis,
    }
def diagnose_spool(jobid: str, sections: List[Dict[str, Any]], raw: str) -> Dict[str, Any]:
    all_text = raw.upper()
    lines = raw.splitlines()
    jobname = ""
    final_rc = ""

    for line in lines:
        m = re.search(r"\$HASP395\s+(\S+)\s+ENDED\s+-\s+RC=(\d+)", line)
        if m:
            jobname, final_rc = m.group(1), m.group(2)
            break

    evidence = []
    for sec in sections:
        for line in sec.get("content", []):
            t = line.strip()
            if any(k in t.upper() for k in ["IGY", "IEF", "IEFC", "HASP", "ABEND", "IEW", "RETURN CODE"]):
                if t not in evidence:
                    evidence.append(t)
            if len(evidence) >= 8:
                break
        if len(evidence) >= 8:
            break

    headline = "Job completed"
    root_cause = "No blocking error was detected."
    impact = "The job reached normal completion."
    fix = "No action needed."
    severity = "success"

    if "IGYPS2113-E" in all_text:
        headline = "COBOL compile failed"
        root_cause = "The compiler found an END-IF without a matching IF."
        impact = "Link-edit and run were skipped because compile returned RC 8."
        fix = "Correct the IF/END-IF pairing in the COBOL source and resubmit."
        severity = "error"
    elif "JCL ERROR" in all_text or re.search(r"IEFC\d+E", raw):
        headline = "JCL validation failed"
        root_cause = "JES rejected the submitted JCL or could not expand it correctly."
        impact = "The job did not proceed normally."
        fix = "Inspect JESJCL and JESYSMSG for the IEFC message and correct the JCL."
        severity = "error"
    elif "ABEND" in all_text:
        headline = "Job ended with ABEND"
        root_cause = "A step ended abnormally during execution."
        impact = "The job failed at runtime."
        fix = "Check the ABEND code in JESYSMSG and investigate the failing step."
        severity = "error"
    elif final_rc in ("0000", "0"):
        headline = "Job completed successfully"
        root_cause = "All steps completed with RC 0."
        impact = "No errors or warnings were detected."
        fix = "No action needed."
        severity = "success"
    elif final_rc and final_rc.isdigit() and int(final_rc) > 0:
        headline = f"Job ended with RC {int(final_rc)}"
        root_cause = "At least one step returned a non-zero condition code."
        impact = "Some processing may have been skipped or partially completed."
        fix = "Inspect the step with the highest RC and review its spool output."
        severity = "warning" if int(final_rc) < 8 else "error"

    ai_prompt = f"""
Explain this IBM Z job result in simple English.

Job ID: {jobid}
Job Name: {jobname or "Unknown"}
Final RC: {final_rc or "Unknown"}

Headline:
{headline}

Root cause:
{root_cause}

Impact:
{impact}

Recommended fix:
{fix}

Evidence:
{chr(10).join(evidence)}
"""

    return {
        "jobid": jobid,
        "jobname": jobname or "Unknown",
        "final_rc": final_rc or "Unknown",
        "headline": headline,
        "root_cause": root_cause,
        "impact": impact,
        "fix": fix,
        "severity": severity,
        "evidence": evidence,
        "ai_prompt": ai_prompt,
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/connection/test")
def test_connection(request: Request):
    config = get_zowe_config(request)

    if not config.get("host") or not config.get("port") or not config.get("user") or not config.get("password"):
        return {
            "ok": False,
            "message": "Missing host, port, user, or password.",
        }

    try:
        output = run_zowe(["zos-jobs", "list", "jobs"], config)
        lines = [line for line in output.splitlines() if line.strip()]

        return {
            "ok": True,
            "message": "Connection successful.",
            "user": config["user"],
            "sample_count": len(lines),
        }

    except HTTPException as exc:
        return {
            "ok": False,
            "message": str(exc.detail),
        }

@app.get("/jobs")
def list_jobs(request: Request):
    config = get_zowe_config(request)
    jobs_data = run_zowe(["zos-jobs", "list", "jobs"], config)
    lines = [line for line in jobs_data.splitlines() if line.strip()]
    return {"jobs_raw": lines, "jobs": parse_jobs(lines)}


@app.get("/jobs/{jobid}/spool")
def view_spool(request: Request, jobid: str):
    config = get_zowe_config(request)
    spool_content = run_zowe(["zos-jobs", "view", "all-spool-content", jobid], config)
    sections = parse_spool_sections(spool_content)
    return {
        "jobid": jobid,
        "spool": spool_content,
        "sections": sections,
        "diagnosis": diagnose_spool(jobid, sections, spool_content),
    }

@app.get("/datasets")
def list_datasets(request: Request, pattern: str = None):
    config = get_zowe_config(request)

    if not pattern:
        pattern = f"{config['user']}.*"

    output = run_zowe(["zos-files", "list", "data-set", pattern], config)
    datasets = [line.strip() for line in output.splitlines() if line.strip()]
    return {"pattern": pattern, "datasets": datasets}


@app.get("/datasets/{dataset_name:path}/members")
def list_members(request: Request, dataset_name: str):
    config = get_zowe_config(request)
    output = run_zowe(["zos-files", "list", "all-members", dataset_name], config)
    members = [line.strip() for line in output.splitlines() if line.strip()]
    return {"dataset": dataset_name, "members": members}


@app.get("/datasets/{dataset_name:path}/members/{member_name}")
def view_member(request: Request, dataset_name: str, member_name: str):
    config = get_zowe_config(request)
    target = f"{dataset_name}({member_name})"
    content = run_zowe(["zos-files", "view", "data-set", target], config)
    return {
        "dataset": dataset_name,
        "member": member_name,
        "dataset_member": target,
        "content": content,
    }

@app.get("/uss/home")
def uss_home(request: Request):
    config = get_zowe_config(request)
    return {
        "user": config["user"],
        "home": user_uss_home(config),
    }

@app.get("/uss")
def list_uss(request: Request, path: str = None):
    config = get_zowe_config(request)

    if not path:
        path = user_uss_home(config)

    output = run_zowe(["zos-files", "list", "uss-files", path], config)
    entries = []

    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue

        parts = line.split()
        name = parts[0] if parts else line
        permissions = parts[1] if len(parts) > 1 else ""
        owner = parts[-1] if len(parts) > 2 else ""

        if name in [".", ".."]:
            continue

        if permissions.startswith("d"):
            entry_type = "directory"
        elif permissions.startswith("l"):
            entry_type = "link"
        else:
            entry_type = "file"

        full_path = path.rstrip("/") + "/" + name if path != "/" else "/" + name

        entries.append({
            "name": name,
            "permissions": permissions,
            "owner": owner,
            "type": entry_type,
            "full_path": full_path,
            "raw": line,
        })

    return {
        "path": path,
        "entries": entries,
    }


@app.get("/uss/file")
def view_uss_file(request: Request, path: str):
    config = get_zowe_config(request)
    content = run_zowe(["zos-files", "view", "uss-file", path], config)
    return {
        "path": path,
        "content": content,
    }

@app.post("/datasets/explain")
def explain_member(request: Request, payload: TextPayload):
    ai_config = get_ai_config(request)

    prompt = (
        "You are Z-Agent, an IBM Z learning assistant.\n"
        "Explain the following z/OS dataset member content for a student.\n\n"

        "Rules:\n"
        "- Identify whether it looks like JCL, COBOL, text, config, or another format.\n"
        "- Explain the purpose of the content.\n"
        "- If it is JCL, explain JOB card, EXEC steps, DD statements, and possible issues.\n"
        "- If it is COBOL, explain program structure and possible compile issues.\n"
        "- Do not invent missing code.\n"
        "- Keep the explanation clear and practical.\n\n"

        "Content:\n"
        f"{payload.content}"
    )

    return explain_with_ai(prompt, ai_config)

@app.post("/jobs/explain")
def explain_spool(request: Request, payload: TextPayload):
    ai_config = get_ai_config(request)

    prompt = (
        "You are Z-Agent, an IBM Z job diagnostic assistant.\n"
        "Your task is to explain the provided job diagnosis in simple English.\n\n"

        "STRICT RULES:\n"
        "1. Use ONLY the provided diagnosis and evidence.\n"
        "2. Do NOT invent errors, warnings, return codes, datasets, steps, or fixes.\n"
        "3. Do NOT treat IEFC653I SUBSTITUTION JCL as an error by itself.\n"
        "4. If the final result says the job completed successfully or Final RC is 0000, say the job succeeded and no fix is needed.\n"
        "5. If the diagnosis says JCL validation failed, explain that the job did not run because JES rejected the JCL.\n"
        "6. If the diagnosis says COBOL compile failed, explain that the source code failed compilation and the program was not built/run.\n"
        "7. If the diagnosis says ABEND, explain that the job started but failed during execution.\n"
        "8. If Final RC is non-zero, explain that at least one step ended with a warning or error depending on the RC.\n"
        "9. If evidence is missing, say that the available evidence is limited. Do not guess.\n\n"

        "OUTPUT FORMAT:\n"
        "1. Final result\n"
        "2. What happened\n"
        "3. Why it happened\n"
        "4. Evidence from spool\n"
        "5. What to fix\n"
        "6. Simple explanation\n\n"

        "STYLE:\n"
        "- Use simple English.\n"
        "- Be short and clear.\n"
        "- Mention exact message codes if they appear in evidence.\n"
        "- Do not give generic advice when a specific fix is already provided.\n\n"

        "JOB DIAGNOSIS AND EVIDENCE:\n"
        f"{payload.content}"
    )

    return explain_with_ai(prompt, ai_config)
    
@app.post("/jobs/submit")
def submit_jcl(request: Request, payload: SubmitPayload):
    config = get_zowe_config(request)
    output = run_zowe(["zos-jobs", "submit", "data-set", payload.dataset_member], config)
    return {
        "submitted": payload.dataset_member,
        "result": output,
    }