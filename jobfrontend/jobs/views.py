import json
import os
from functools import wraps
from urllib.parse import quote

import requests
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt


FASTAPI_URL = os.getenv("FASTAPI_URL", "http://127.0.0.1:3001")


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
        "provider": "server_ollama",
        "model": "llama3.2:3b",
        "api_key": "",
        "ollama_url": "http://127.0.0.1:11434/api/generate",
    })


def ai_headers_from_profile(profile):
    if not profile:
        return {}

    return {
        "X-AI-Provider": profile.get("provider", "server_ollama"),
        "X-AI-Model": profile.get("model", "llama3.2:3b"),
        "X-AI-API-Key": profile.get("api_key", ""),
        "X-Ollama-URL": profile.get("ollama_url", "http://127.0.0.1:11434/api/generate"),
    }


def request_headers(request):
    headers = {}
    headers.update(zowe_headers_from_profile(get_zowe_profile(request)))
    headers.update(ai_headers_from_profile(get_ai_profile(request)))
    return headers


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
        "ai_provider": "server_ollama",
        "ai_model": "llama3.2:3b",
        "ollama_url": "http://127.0.0.1:11434/api/generate",
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
    ai_provider = request.POST.get("ai_provider", "server_ollama").strip()
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
            "ollama_url": ollama_url or "http://127.0.0.1:11434/api/generate",
        }
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
def ai_settings_view(request):
    current = get_ai_profile(request)

    if request.method == "GET":
        return render(request, "jobs/ai_settings.html", {
            "form": current,
            "saved": False,
            "zowe_user": get_zowe_profile(request).get("user"),
        })

    provider = request.POST.get("ai_provider", "server_ollama").strip()
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
        "ollama_url": ollama_url or "http://127.0.0.1:11434/api/generate",
    }

    return render(request, "jobs/ai_settings.html", {
        "form": request.session["ai_profile"],
        "saved": True,
        "zowe_user": get_zowe_profile(request).get("user"),
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
        return JsonResponse(result, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON received"}, status=400)
    except requests.exceptions.RequestException as exc:
        return JsonResponse({"error": f"Failed to explain member: {exc}"}, status=500)


@csrf_exempt
@require_zowe_session
def submit_jcl(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body)
        dataset_member = data.get("dataset_member", "").strip()
        if not dataset_member:
            return JsonResponse({"error": "No dataset member provided"}, status=400)

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
        return JsonResponse({"error": f"Failed to submit JCL: {exc}"}, status=500)