import json
import os
from functools import wraps
from urllib.parse import quote
from .audit import write_audit_log

from .safety import get_safety_mode, is_action_allowed, set_safety_mode, action_requires_approval

import requests
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt


FASTAPI_URL = os.getenv("FASTAPI_URL", "http://127.0.0.1:3001")

# Default AI provider / Ollama URL for fresh sessions.
# Docker server mode uses the z-agent-ollama container on the Docker network:
#   http://ollama:11434/api/generate
# For local non-Docker development, change this to:
#   http://127.0.0.1:11434/api/generate
DEFAULT_AI_PROVIDER = "custom_ollama"
DEFAULT_AI_MODEL = "llama3.2:3b"
DEFAULT_OLLAMA_URL = "http://ollama:11434/api/generate"


def get_zowe_profile(request):
    return request.session.get("zowe_profile")


def has_zowe_session(request):
    return bool(get_zowe_profile(request))


def zowe_headers_from_profile(profile):
    """
    Convert the current user's IBM Z connection profile into headers
    that Django sends to FastAPI.
    """
    if not profile:
        return {}

    return {
        "X-Zowe-Host": profile.get("host", ""),
        "X-Zowe-Port": str(profile.get("port", "")),
        "X-Zowe-User": profile.get("user", ""),
        "X-Zowe-Password": profile.get("password", ""),
        "X-Zowe-RU": profile.get("ru", "false"),
    }


def get_ai_profile(request):
    return request.session.get("ai_profile", {
        "provider": DEFAULT_AI_PROVIDER,
        "model": DEFAULT_AI_MODEL,
        "api_key": "",
        "ollama_url": DEFAULT_OLLAMA_URL,
    })


def ai_headers_from_profile(profile):
    if not profile:
        return {}

    return {
        "X-AI-Provider": profile.get("provider", DEFAULT_AI_PROVIDER),
        "X-AI-Model": profile.get("model", DEFAULT_AI_MODEL),
        "X-AI-API-Key": profile.get("api_key", ""),
        "X-Ollama-URL": profile.get("ollama_url", DEFAULT_OLLAMA_URL),
    }


def request_headers(request):
    headers = {}
    headers.update(zowe_headers_from_profile(get_zowe_profile(request)))
    headers.update(ai_headers_from_profile(get_ai_profile(request)))
    return headers


_ZOWE_HEADER_KEYS = (
    "X-Zowe-Host", "X-Zowe-Port", "X-Zowe-User", "X-Zowe-Password", "X-Zowe-RU",
)
_AI_HEADER_KEYS = (
    "X-AI-Provider", "X-AI-Model", "X-AI-API-Key", "X-Ollama-URL",
)
_EXTRA_DEVOPS_HEADER_KEYS = ("X-Ownership-Rules-Path",)


def devops_headers(request):
    """Build headers for DevOps pipeline callers.

    Pipelines pass IBM Z / AI credentials directly via request headers instead
    of a web session, so we forward the incoming X-Zowe-* / X-AI-* headers and
    fall back to the session profile only when the header is absent.
    """
    headers = request_headers(request)
    for key in _ZOWE_HEADER_KEYS + _AI_HEADER_KEYS + _EXTRA_DEVOPS_HEADER_KEYS:
        incoming = request.headers.get(key)
        if incoming:
            headers[key] = incoming
    return headers


def devops_backend_post(request, path, payload, timeout=300):
    response = requests.post(
        f"{FASTAPI_URL}{path}",
        json=payload,
        timeout=timeout,
        headers=devops_headers(request),
    )
    response.raise_for_status()
    return response.json()


def zowe_headers(request):
    return request_headers(request)

def require_zowe_session(view_func):
    """
    Protect Z-Agent pages.
    If user has not entered IBM Z credentials, send them to /setup/.
    For AJAX/POST endpoints, return JSON error instead of redirect.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not has_zowe_session(request):
            if request.method == "POST":
                return JsonResponse(
                    {"error": "No IBM Z connection. Please connect first."},
                    status=401,
                )
            return redirect("setup")
        return view_func(request, *args, **kwargs)

    return wrapper


def backend_get(request, path, timeout=20, params=None):
    response = requests.get(
        f"{FASTAPI_URL}{path}",
        timeout=timeout,
        params=params,
        headers=request_headers(request),
    )
    response.raise_for_status()
    return response.json()


def backend_post(request, path, payload, timeout=90):
    response = requests.post(
        f"{FASTAPI_URL}{path}",
        json=payload,
        timeout=timeout,
        headers=request_headers(request),
    )
    response.raise_for_status()
    return response.json()

def classify_retcode(retcode, status):
    raw = f"{retcode} {status}".upper()
    if "CC 0000" in raw:
        return "success"
    if "ABEND" in raw or "JCL ERROR" in raw or "ERROR" in raw:
        return "error"
    if "ACTIVE" in raw:
        return "info"
    return "warning"


def home(request):
    if has_zowe_session(request):
        return redirect("job_list")
    return redirect("setup")


@csrf_exempt
def health(request):
    """Unauthenticated health endpoint for load balancers and orchestrators.

    Returns 200 JSON when the Django frontend process is alive. This does not
    probe the FastAPI backend or IBM Z so it stays safe to call frequently from
    a Docker healthcheck or reverse proxy without recording audit entries.
    """
    return JsonResponse({
        "status": "ok",
        "service": "z-agent-frontend",
        "version": "v1.2.0-preview",
    })


def setup_view(request):
    """
    First screen of product mode.
    User enters IBM Z / zOSMF credentials.
    We test the connection through FastAPI, then store credentials in Django session.
    """
    defaults = {
        "host": os.getenv("ZOWE_HOST", "204.90.115.200"),
        "port": os.getenv("ZOWE_PORT", "10443"),
        "user": os.getenv("ZOWE_USER", ""),
        "allow_self_signed": True,
        "ai_provider": DEFAULT_AI_PROVIDER,
        "ai_model": DEFAULT_AI_MODEL,
        "ollama_url": DEFAULT_OLLAMA_URL,
    }

    if request.method == "GET":
        return render(request, "jobs/setup.html", {
            "form": defaults,
            "error": None,
        })

    host = request.POST.get("host", "").strip()
    port = request.POST.get("port", "").strip()
    user = request.POST.get("user", "").strip().upper()
    password = request.POST.get("password", "")
    allow_self_signed = request.POST.get("allow_self_signed") == "on"
    ai_provider = request.POST.get("ai_provider", DEFAULT_AI_PROVIDER).strip()
    ai_model = request.POST.get("ai_model", "").strip()
    ai_api_key = request.POST.get("ai_api_key", "").strip()
    ollama_url = request.POST.get("ollama_url", "").strip()

    # Zowe CLI option:
    # --ru false means rejectUnauthorized=false, useful for IBM Z Xplore/self-signed certs.
    ru = "false" if allow_self_signed else "true"

    form = {
        "host": host,
        "port": port,
        "user": user,
        "allow_self_signed": allow_self_signed,
        "ai_provider": ai_provider,
        "ai_model": ai_model,
        "ai_api_key": "",
        "ollama_url": ollama_url,
    }

    if not host or not port or not user or not password:
        return render(request, "jobs/setup.html", {
            "form": form,
            "error": "Please fill host, port, user ID, and password.",
        })

    profile = {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "ru": ru,
    }

    try:
        # Test the connection before saving it.
        response = requests.get(
            f"{FASTAPI_URL}/connection/test",
            timeout=30,
            headers=zowe_headers_from_profile(profile),
        )
        response.raise_for_status()
        result = response.json()

        if not result.get("ok"):
            return render(request, "jobs/setup.html", {
                "form": form,
                "error": result.get("message", "Connection test failed."),
            })

        request.session["zowe_profile"] = profile

        # For now AI settings are simple. We will expand this later.
        if ai_provider == "rule_based":
            default_model = "none"
        elif ai_provider in {"server_ollama", "custom_ollama"}:
            default_model = "llama3.2:3b"
        elif ai_provider == "claude":
            default_model = "claude-3-5-haiku-latest"
        elif ai_provider == "openai":
            default_model = "gpt-4.1-mini"
        elif ai_provider == "gemini":
            default_model = "gemini-2.5-flash"
        else:
            ai_provider = "rule_based"
            default_model = "none"

        request.session["ai_profile"] = {
            "provider": ai_provider,
            "model": ai_model or default_model,
            "api_key": ai_api_key,
            "ollama_url": ollama_url or DEFAULT_OLLAMA_URL,
        }

        request.session["safety_mode"] = "READ_ONLY"

        return redirect("job_list")

    except requests.exceptions.RequestException as exc:
        return render(request, "jobs/setup.html", {
            "form": form,
            "error": f"Connection test failed: {exc}",
        })


def logout_view(request):
    request.session.flush()
    return redirect("setup")

@require_zowe_session
def safety_settings_view(request):
    current_mode = get_safety_mode(request)

    if request.method == "GET":
        write_audit_log(
            request,
            action="VIEW_SAFETY_SETTINGS",
            target="Safety Settings",
            status="ALLOWED",
            details="Viewed safety settings page",
        )
        return render(request, "jobs/safety_settings.html", {
            "safety_mode": current_mode,
            "saved": False,
            "zowe_user": get_zowe_profile(request).get("user"),
        })

    requested_mode = request.POST.get("safety_mode", "READ_ONLY").strip()
    new_mode = set_safety_mode(request, requested_mode)

    write_audit_log(
        request,
        action="CHANGE_SAFETY_MODE",
        target="Safety Settings",
        status="ALLOWED",
        details=f"Safety mode changed from {current_mode} to {new_mode}",
    )

    return render(request, "jobs/safety_settings.html", {
        "safety_mode": new_mode,
        "saved": True,
        "zowe_user": get_zowe_profile(request).get("user"),
    })

@require_zowe_session
def ai_settings_view(request):
    current = get_ai_profile(request)

    if request.method == "GET":
        return render(request, "jobs/ai_settings.html", {
            "form": current,
            "saved": False,
            "zowe_user": get_zowe_profile(request).get("user"),
        })

    provider = request.POST.get("ai_provider", DEFAULT_AI_PROVIDER).strip()
    model = request.POST.get("ai_model", "").strip()
    api_key = request.POST.get("ai_api_key", "").strip()
    ollama_url = request.POST.get("ollama_url", "").strip()

    if provider == "rule_based":
        default_model = "none"
    elif provider in {"server_ollama", "custom_ollama"}:
        default_model = "llama3.2:3b"
    elif provider == "claude":
        default_model = "claude-3-5-haiku-latest"
    elif provider == "openai":
        default_model = "gpt-4.1-mini"
    elif provider == "gemini":
        default_model = "gemini-2.5-flash"
    else:
        provider = "rule_based"
        default_model = "none"

    # If user leaves API key empty on settings page, keep old key.
    old_api_key = current.get("api_key", "")
    final_api_key = api_key or old_api_key

    request.session["ai_profile"] = {
        "provider": provider,
        "model": model or default_model,
        "api_key": final_api_key,
        "ollama_url": ollama_url or DEFAULT_OLLAMA_URL,
    }

    return render(request, "jobs/ai_settings.html", {
        "form": request.session["ai_profile"],
        "saved": True,
        "zowe_user": get_zowe_profile(request).get("user"),
    })

@require_zowe_session
def audit_logs(request):
    from .models import AuditLog

    write_audit_log(
        request,
        action="VIEW_AUDIT_LOGS",
        target="Audit Logs",
        status="ALLOWED",
        details="Viewed audit log page",
    )

    logs = AuditLog.objects.all().order_by("-created_at")[:100]

    return render(request, "jobs/audit_logs.html", {
        "logs": logs,
        "zowe_user": get_zowe_profile(request).get("user"),
        "safety_mode": get_safety_mode(request),
    })

@require_zowe_session
def job_list(request):
    try:
        data = backend_get(request, "/jobs", timeout=20)
        jobs = data.get("jobs", [])

        for job in jobs:
            job["severity"] = classify_retcode(
                job.get("retcode", ""),
                job.get("status", ""),
            )

        write_audit_log(
            request,
            action="VIEW_JOBS",
            target="Jobs dashboard",
            status="ALLOWED",
            details=f"Viewed {len(jobs)} jobs",
        )

        return render(request, "jobs/job_list.html", {
            "jobs": jobs,
            "zowe_user": get_zowe_profile(request).get("user"),
        })

    except requests.exceptions.ConnectionError:
        return HttpResponse(
            "Cannot connect to FastAPI backend at http://127.0.0.1:3001",
            status=500,
        )
    except requests.exceptions.RequestException as exc:
        return HttpResponse(str(exc), status=500)
    except (json.JSONDecodeError, KeyError) as exc:
        return HttpResponse(f"Backend response was invalid: {exc}", status=500)


@require_zowe_session
def view_spool(request, jobid):
    try:
        data = backend_get(request, f"/jobs/{jobid}/spool", timeout=60)
        write_audit_log(
            request,
            action="VIEW_SPOOL",
            target=jobid,
            status="ALLOWED",
            details="Viewed job spool output",
        )
        return render(request, "jobs/job_spool.html", {
            "jobid": jobid,
            "spool_sections": data.get("sections", []),
            "diagnosis": data.get("diagnosis", {}),
            "raw_spool": data.get("spool", ""),
            "zowe_user": get_zowe_profile(request).get("user"),
        })
    except requests.exceptions.RequestException as exc:
        return HttpResponse(str(exc), status=500)
    except (json.JSONDecodeError, KeyError) as exc:
        return HttpResponse(f"Backend response was invalid: {exc}", status=500)


@require_zowe_session
def explorer(request):
    zowe_user = get_zowe_profile(request).get("user", "")
    default_pattern = f"{zowe_user}.*" if zowe_user else "*"

    pattern = request.GET.get("pattern", default_pattern)
    selected_dataset = request.GET.get("dataset")
    selected_member = request.GET.get("member")

    context = {
        "pattern": pattern,
        "datasets": [],
        "selected_dataset": selected_dataset,
        "members": [],
        "selected_member": selected_member,
        "member_content": None,
        "dataset_member": None,
        "zowe_user": zowe_user,
    }

    try:
        dataset_data = backend_get(
            request,
            "/datasets",
            params={"pattern": pattern},
            timeout=30,
        )
        context["datasets"] = dataset_data.get("datasets", [])

        if selected_dataset:
            member_data = backend_get(
                request,
                f"/datasets/{quote(selected_dataset, safe='')}/members",
                timeout=30,
            )
            context["members"] = member_data.get("members", [])

        if selected_dataset and selected_member:
            detail = backend_get(
                request,
                f"/datasets/{quote(selected_dataset, safe='')}/members/{quote(selected_member, safe='')}",
                timeout=30,
            )
            context["member_content"] = detail.get("content", "")
            context["dataset_member"] = detail.get("dataset_member", "")

    except requests.exceptions.RequestException as exc:
        context["error"] = str(exc)
    write_audit_log(
        request,
        action="VIEW_DATASET",
        target=selected_dataset or pattern,
        status="ALLOWED",
        details="Viewed dataset explorer",
    )

    return render(request, "jobs/explorer.html", context)


@require_zowe_session
def member_detail(request, dataset_name, member_name):
    try:
        detail = backend_get(
            request,
            f"/datasets/{quote(dataset_name, safe='')}/members/{quote(member_name, safe='')}",
            timeout=30,
        )
        return HttpResponse(
            f"""
            <html>
            <body style="background:#03070f;color:#e8f4ff;font-family:Arial;padding:24px;">
                <h1>{detail.get('dataset_member', 'Unknown member')}</h1>
                <pre style="white-space:pre-wrap;line-height:1.6;background:#0c1526;padding:16px;border-radius:12px;">{detail.get('content', '')}</pre>
            </body>
            </html>
            """
        )
    except requests.exceptions.RequestException as exc:
        return HttpResponse(str(exc), status=500)


@require_zowe_session
def uss_browser(request):
    path = request.GET.get("path")
    file_path = request.GET.get("file")

    context = {
        "path": path,
        "home_path": "/",
        "entries": [],
        "file_path": file_path,
        "file_content": None,
        "error": None,
        "zowe_user": get_zowe_profile(request).get("user"),
    }

    try:
        home_data = backend_get(request, "/uss/home", timeout=15)
        home_path = home_data.get("home", "/")
        context["home_path"] = home_path

        if not path:
            path = home_path

        context["path"] = path

        data = backend_get(
            request,
            "/uss",
            params={"path": path},
            timeout=60,
        )
        context["entries"] = data.get("entries", [])

        if file_path:
            file_data = backend_get(
                request,
                "/uss/file",
                params={"path": file_path},
                timeout=60,
            )
            context["file_content"] = file_data.get("content", "")

    except requests.exceptions.RequestException as exc:
        context["error"] = str(exc)
    write_audit_log(
        request,
        action="VIEW_USS",
        target=context.get("path") or "/",
        status="ALLOWED",
        details="Viewed USS browser",
    )    

    return render(request, "jobs/uss_browser.html", context)


@csrf_exempt
@require_zowe_session
def send_spool_to_ollama(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body)
        prompt = data.get("prompt", "").strip()
        if not prompt:
            return JsonResponse({"error": "No prompt received"}, status=400)

        result = backend_post(request, "/jobs/explain", {"content": prompt}, timeout=300)
        write_audit_log(
            request,
            action="AI_EXPLAIN",
            target="spool",
            status="ALLOWED",
            details="AI explanation requested for spool content",
        )
        return JsonResponse(result, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON received"}, status=400)
    except requests.exceptions.RequestException as exc:
        return JsonResponse({"error": f"Failed to reach FastAPI backend: {exc}"}, status=500)


@csrf_exempt
@require_zowe_session
def explain_member(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body)
        content = data.get("content", "").strip()
        if not content:
            return JsonResponse({"error": "No member content received"}, status=400)

        result = backend_post(request, "/datasets/explain", {"content": content}, timeout=300)
        write_audit_log(
            request,
            action="AI_EXPLAIN",
            target="dataset member",
            status="ALLOWED",
            details="AI explanation requested for dataset member",
        )
        return JsonResponse(result, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON received"}, status=400)
    except requests.exceptions.RequestException as exc:
        return JsonResponse({"error": f"Failed to explain member: {exc}"}, status=500)


@csrf_exempt
@require_zowe_session
def explain_spool_ai(request):
    """v0.3.0 AI Operations Preview - structured spool explanation.

    Proxies to the FastAPI /api/agent/explain-spool endpoint, writes an
    AI_EXPLAIN_SPOOL audit log entry (metadata only - never raw spool), and
    attaches an audit_id to the response shown in the UI/API.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON received"}, status=400)

    job_id = str(data.get("job_id", "")).strip()
    spool_text = str(data.get("spool_text", ""))

    safety_mode = get_safety_mode(request)
    if not is_action_allowed("AI_EXPLAIN_SPOOL", safety_mode):
        write_audit_log(
            request,
            action="AI_EXPLAIN_SPOOL",
            target=job_id or "unknown",
            status="BLOCKED",
            details=f"AI spool explanation blocked by safety mode: {safety_mode}",
        )
        return JsonResponse(
            {
                "status": "error",
                "message": f"AI explanation is blocked in {safety_mode} mode.",
                "ai_used": False,
            },
            status=403,
        )

    try:
        result = backend_post(
            request,
            "/api/agent/explain-spool",
            {"job_id": job_id, "spool_text": spool_text},
            timeout=300,
        )
    except requests.exceptions.RequestException:
        result = {
            "status": "error",
            "message": "AI explanation is currently unavailable.",
            "ai_used": False,
        }

    ai_used = bool(result.get("ai_used"))
    masked = bool(result.get("masked"))
    model = result.get("model", "")
    audit_status = "ALLOWED" if ai_used else "FAILED"
    details = (
        f"AI explain spool; ai_used={'yes' if ai_used else 'no'}; "
        f"model={model or 'n/a'}; masked={'yes' if masked else 'no'}; "
        "raw spool not stored"
    )

    audit_entry = write_audit_log(
        request,
        action="AI_EXPLAIN_SPOOL",
        target=job_id or "unknown",
        status=audit_status,
        details=details,
    )

    audit_id = f"AUD-{audit_entry.id:06d}" if audit_entry else None
    result["job_id"] = job_id
    result["masked"] = True
    result["audit_id"] = audit_id
    return JsonResponse(result, status=200)


@csrf_exempt
@require_zowe_session
def submit_jcl(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body)
        dataset_member = data.get("dataset_member", "").strip()
        approved = bool(data.get("approved", False))

        if not dataset_member:
            return JsonResponse({"error": "No dataset member provided"}, status=400)

        safety_mode = get_safety_mode(request)

        if action_requires_approval("SUBMIT_JCL", safety_mode) and not approved:
            write_audit_log(
                request,
                action="SUBMIT_JCL",
                target=dataset_member,
                status="APPROVAL_REQUIRED",
                details="JCL submit requires explicit approval",
            )
            return JsonResponse(
                {
                    "error": "Approval required before submitting JCL.",
                    "safety_mode": safety_mode,
                    "status": "APPROVAL_REQUIRED",
                    "requires_approval": True,
                },
                status=409,
            )

        if not is_action_allowed("SUBMIT_JCL", safety_mode, approved=approved):
            write_audit_log(
                request,
                action="SUBMIT_JCL",
                target=dataset_member,
                status="BLOCKED",
                details=f"JCL submit blocked by safety mode: {safety_mode}",
            )
            return JsonResponse(
                {
                    "error": f"JCL submit is blocked in {safety_mode} mode.",
                    "safety_mode": safety_mode,
                    "status": "BLOCKED",
                },
                status=403,
            )

        write_audit_log(
            request,
            action="SUBMIT_JCL",
            target=dataset_member,
            status="ALLOWED",
            details=f"JCL submit allowed by safety mode: {safety_mode}",
        )

        result = backend_post(
            request,
            "/jobs/submit",
            {"dataset_member": dataset_member},
            timeout=90,
        )

        return JsonResponse(result, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON received"}, status=400)

    except requests.exceptions.RequestException as exc:
        write_audit_log(
            request,
            action="SUBMIT_JCL",
            target="unknown",
            status="FAILED",
            details=f"Backend error during JCL submit: {exc}",
        )
        return JsonResponse({"error": "Failed to submit JCL. Check backend logs."}, status=500)


# ---------------------------------------------------------------------------
# v0.5.0 DevOps Integration Preview
# ---------------------------------------------------------------------------

def _safe_error_json(message="DevOps request could not be processed.", status=500):
    return JsonResponse({"status": "error", "message": message}, status=status)


def _audit_id_for(entry):
    return f"AUD-{entry.id:06d}" if entry else None


@csrf_exempt
def devops_job_summary(request):
    """Pipeline-friendly structured job summary proxy (v0.5.0).

    No web session is required: pipelines pass IBM Z / AI headers directly.
    Writes a DEVOPS_JOB_SUMMARY audit log entry (metadata only) and attaches
    an audit_id to the response.
    """
    if request.method != "POST":
        return _safe_error_json("Invalid request method", status=405)

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return _safe_error_json("Invalid JSON received", status=400)

    job_id = str(data.get("job_id", "")).strip()
    job_name = str(data.get("job_name", "")).strip()
    include_ai = bool(data.get("include_ai_explanation", True))

    safety_mode = get_safety_mode(request)
    if not is_action_allowed("DEVOPS_JOB_SUMMARY", safety_mode):
        write_audit_log(
            request, action="DEVOPS_JOB_SUMMARY", target=job_id or "unknown",
            status="BLOCKED",
            details=f"Job summary blocked by safety mode: {safety_mode}",
        )
        return JsonResponse(
            {"status": "error", "message": f"Job summary blocked in {safety_mode} mode."},
            status=403,
        )

    try:
        result = devops_backend_post(
            request, "/api/devops/job-summary",
            {"job_id": job_id, "job_name": job_name,
             "include_ai_explanation": include_ai},
        )
    except requests.exceptions.RequestException:
        result = {
            "job_id": job_id, "job_name": job_name, "status": "UNKNOWN",
            "return_code": "UNKNOWN", "result": "unknown",
            "ai_used": False,
            "message": "Job summary is currently unavailable.",
            "safe_to_continue": False,
        }

    ai_used = bool(result.get("ai_used"))
    audit_status = "ALLOWED" if result.get("status") != "UNKNOWN" else "FAILED"
    entry = write_audit_log(
        request, action="DEVOPS_JOB_SUMMARY", target=job_id or "unknown",
        status=audit_status,
        details=(f"job_name={job_name or 'n/a'}; ai_used={'yes' if ai_used else 'no'}; "
                 f"status={result.get('status', 'unknown')}; raw spool not stored"),
    )
    result["audit_id"] = _audit_id_for(entry)
    return JsonResponse(result, status=200)


@csrf_exempt
def devops_incident_summary(request):
    """Incident first-pass summary proxy (v0.5.0).

    Produces a paste-ready structured summary. No web session required.
    Writes a DEVOPS_INCIDENT_SUMMARY audit log entry and attaches an audit_id.
    """
    if request.method != "POST":
        return _safe_error_json("Invalid request method", status=405)

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return _safe_error_json("Invalid JSON received", status=400)

    job_id = str(data.get("job_id", "")).strip()
    job_name = str(data.get("job_name", "")).strip()
    spool_text = str(data.get("spool_text", ""))
    include_ai = bool(data.get("include_ai_explanation", True))

    safety_mode = get_safety_mode(request)
    if not is_action_allowed("DEVOPS_INCIDENT_SUMMARY", safety_mode):
        write_audit_log(
            request, action="DEVOPS_INCIDENT_SUMMARY", target=job_id or "unknown",
            status="BLOCKED",
            details=f"Incident summary blocked by safety mode: {safety_mode}",
        )
        return JsonResponse(
            {"status": "error", "message": f"Incident summary blocked in {safety_mode} mode."},
            status=403,
        )

    try:
        result = devops_backend_post(
            request, "/api/devops/incident-summary",
            {"job_id": job_id, "job_name": job_name, "spool_text": spool_text,
             "include_ai_explanation": include_ai},
        )
    except requests.exceptions.RequestException:
        result = {
            "title": f"IBM Z job {job_name or job_id} summary unavailable",
            "severity": "medium",
            "summary": "z-agent could not generate an incident summary.",
            "evidence": "",
            "recommended_owner": "Unknown - configure ownership rules",
            "suggested_next_step": "Check z-agent backend availability.",
        }

    entry = write_audit_log(
        request, action="DEVOPS_INCIDENT_SUMMARY", target=job_id or "unknown",
        status="ALLOWED",
        details=(f"job_name={job_name or 'n/a'}; "
                 f"severity={result.get('severity', 'unknown')}; "
                 f"raw spool not stored"),
    )
    result["audit_id"] = _audit_id_for(entry)
    return JsonResponse(result, status=200)


@csrf_exempt
def devops_notify(request):
    """Webhook notification proxy with dry-run safety default (v0.5.0).

    dry_run defaults to True so pipelines never accidentally send real network
    requests. Real sends (dry_run=False) are gated by the safety mode for the
    DEVOPS_NOTIFY_SENT risky action. All paths write an audit log entry; raw
    spool is never stored.
    """
    if request.method != "POST":
        return _safe_error_json("Invalid request method", status=405)

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return _safe_error_json("Invalid JSON received", status=400)

    webhook_url = str(data.get("webhook_url", "")).strip()
    job_id = str(data.get("job_id", "")).strip()
    job_name = str(data.get("job_name", "")).strip()
    summary = str(data.get("summary", ""))
    dry_run = bool(data.get("dry_run", True))

    safety_mode = get_safety_mode(request)

    if dry_run:
        action = "DEVOPS_NOTIFY_DRY_RUN"
        if not is_action_allowed(action, safety_mode):
            write_audit_log(request, action=action, target=job_id or "unknown",
                            status="BLOCKED",
                            details=f"Notify dry-run blocked by safety mode: {safety_mode}")
            return JsonResponse(
                {"status": "error", "message": f"Notify blocked in {safety_mode} mode."},
                status=403,
            )
        audit_action = "DEVOPS_NOTIFY_DRY_RUN"
        audit_status = "ALLOWED"
    else:
        action = "DEVOPS_NOTIFY_SENT"
        if not is_action_allowed(action, safety_mode, approved=True):
            write_audit_log(
                request, action="DEVOPS_NOTIFY_SENT", target=job_id or "unknown",
                status="BLOCKED",
                details=(f"Real webhook notify blocked by safety mode: {safety_mode}; "
                         "use EXECUTE mode or dry_run=true"),
            )
            return JsonResponse(
                {"status": "error",
                 "message": (f"Real webhook send is blocked in {safety_mode} mode. "
                             "Use EXECUTE mode or dry_run=true."),
                 "dry_run": True},
                status=403,
            )
        audit_action = "DEVOPS_NOTIFY_SENT"

    try:
        result = devops_backend_post(
            request, "/api/devops/notify",
            {"webhook_url": webhook_url, "job_id": job_id, "job_name": job_name,
             "summary": summary, "dry_run": dry_run},
        )
    except requests.exceptions.RequestException:
        result = {"status": "error",
                  "message": "Webhook notification service is currently unavailable."}
        if not dry_run:
            audit_action = "DEVOPS_NOTIFY_FAILED"

    audit_status = "ALLOWED" if result.get("status") in ("dry_run", "sent") else "FAILED"
    if not dry_run and result.get("status") == "error":
        audit_action = "DEVOPS_NOTIFY_FAILED"
        audit_status = "FAILED"

    entry = write_audit_log(
        request, action=audit_action, target=job_id or "unknown",
        status=audit_status,
        details=(f"job_name={job_name or 'n/a'}; dry_run={'yes' if dry_run else 'no'}; "
                 f"notify_status={result.get('status', 'unknown')}; "
                 "no secrets in payload; raw spool not stored"),
    )
    result["audit_id"] = _audit_id_for(entry)
    return JsonResponse(result, status=200)


# ---------------------------------------------------------------------------
# v0.7.0 Performance Insights Preview
# ---------------------------------------------------------------------------

@csrf_exempt
def performance_insights_api(request):
    """API proxy for performance insights (v0.7.0).

    No web session required for the API (pipelines pass headers). Writes a
    PERFORMANCE_INSIGHTS_ANALYSIS audit log entry with metadata only (system
    name, period, ratio names, ai_used, benchmark_mode) — raw metrics are
    never stored.

    Always returns JsonResponse (never HTML) so the browser's fetch().json()
    does not see an HTML 500/redirect page.
    """
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "error": "Invalid request method",
             "message": "Invalid request method"}, status=405,
        )

    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse(
            {"status": "error", "error": "Invalid JSON",
             "message": "Invalid JSON received"}, status=400,
        )
    except Exception:
        return JsonResponse(
            {"status": "error", "error": "Invalid JSON",
             "message": "Invalid JSON received"}, status=400,
        )

    system_name = str(data.get("system_name", "")).strip()
    period = str(data.get("period", "")).strip()
    metrics = data.get("metrics", {})
    if not isinstance(metrics, dict):
        metrics = {}
    include_ai = bool(data.get("include_ai_explanation", True))

    safety_mode = get_safety_mode(request)
    if not is_action_allowed("PERFORMANCE_INSIGHTS_ANALYSIS", safety_mode):
        write_audit_log(
            request, action="PERFORMANCE_INSIGHTS_ANALYSIS",
            target=system_name or "unknown", status="BLOCKED",
            details=f"Performance insights blocked by safety mode: {safety_mode}",
        )
        return JsonResponse(
            {"status": "error",
             "error": f"Performance insights blocked in {safety_mode} mode.",
             "message": f"Performance insights blocked in {safety_mode} mode."},
            status=403,
        )

    try:
        result = devops_backend_post(
            request, "/api/performance/insights",
            {"system_name": system_name, "period": period, "metrics": metrics,
             "include_ai_explanation": include_ai},
        )
    except requests.exceptions.RequestException as exc:
        return JsonResponse(
            {"status": "error",
             "error": "Failed to analyze performance metrics",
             "message": "Failed to analyze performance metrics",
             "detail": "z-agent backend is currently unavailable.",
             "system_name": system_name, "period": period,
             "overall_grade": "AVG", "overall_score": 0,
             "ratios": [], "benchmark_mode": "local-scale-only"}, status=502,
        )
    except Exception as exc:
        return JsonResponse(
            {"status": "error",
             "error": "Failed to analyze performance metrics",
             "message": "Failed to analyze performance metrics",
             "detail": str(exc) or "Unexpected error during analysis."},
            status=500,
        )

    ai_available = bool(result.get("ai_explanation", {}).get("available"))
    applicable_benchmark_mode = str(result.get("benchmark_mode", "local-scale-only"))

    try:
        # Build safe audit metadata. Never store raw metric values.
        from agent.performance_insights import ratio_names, metrics_summary_for_audit
        names = ratio_names(result)
        meta = metrics_summary_for_audit(metrics)

        entry = write_audit_log(
            request, action="PERFORMANCE_INSIGHTS_ANALYSIS",
            target=system_name or "unknown",
            status="ALLOWED" if "ratios" in result else "FAILED",
            details=(f"period={period or 'n/a'}; ratios={','.join(names)}; "
                     f"ai_used={'yes' if ai_available else 'no'}; "
                     f"benchmark_mode={applicable_benchmark_mode}; {meta}"),
        )
        result["audit_id"] = _audit_id_for(entry)
    except Exception:
        result["audit_id"] = None

    return JsonResponse(result, status=200)


@require_zowe_session
def performance_insights_view(request):
    """Simple UI page for the Performance Insights Preview (v0.7.0)."""
    return render(request, "jobs/performance_insights.html", {
        "zowe_user": get_zowe_profile(request).get("user") if get_zowe_profile(request) else None,
        "safety_mode": get_safety_mode(request),
    })