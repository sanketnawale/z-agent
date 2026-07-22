"""
Safety modes and action allow-lists for z-agent.

Read/analyze actions (SAFE_READ_ACTIONS) are allowed in every safety mode,
including READ_ONLY. AI_EXPLAIN_SPOOL is treated as a read-only action because
it only runs AI analysis over already-available spool text and does not modify
anything on IBM Z.
"""

SAFE_READ_ACTIONS = {
    "VIEW_JOBS",
    "VIEW_SPOOL",
    "VIEW_DATASET",
    "VIEW_USS",
    "AI_EXPLAIN",
    "AI_EXPLAIN_SPOOL",
    "VIEW_AUDIT_LOGS",
    "VIEW_SAFETY_SETTINGS",
    "CHANGE_SAFETY_MODE",
}

RISKY_ACTIONS = {
    "SUBMIT_JCL",
    "CANCEL_JOB",
    "DELETE_DATASET",
    "WRITE_USS_FILE",
}

SAFETY_MODES = {
    "READ_ONLY",
    "APPROVAL_REQUIRED",
    "EXECUTE",
}


def get_safety_mode(request):
    return request.session.get("safety_mode", "READ_ONLY")


def set_safety_mode(request, mode):
    if mode not in SAFETY_MODES:
        mode = "READ_ONLY"
    request.session["safety_mode"] = mode
    return mode


def is_action_allowed(action, safety_mode, approved=False):
    if action in SAFE_READ_ACTIONS:
        return True

    if action in RISKY_ACTIONS:
        if safety_mode == "READ_ONLY":
            return False

        if safety_mode == "APPROVAL_REQUIRED":
            return bool(approved)

        if safety_mode == "EXECUTE":
            return True

    return False


def action_requires_approval(action, safety_mode):
    return action in RISKY_ACTIONS and safety_mode == "APPROVAL_REQUIRED"


def mask_secret(value):
    if not value:
        return value
    value = str(value)
    if len(value) <= 4:
        return "****"
    return value[:2] + "****" + value[-2:]


def mask_text(text):
    if not text:
        return text

    text = str(text)

    sensitive_words = [
        "password",
        "api_key",
        "token",
        "secret",
        "authorization",
        "x-zowe-password",
        "x-ai-api-key",
    ]

    lines = []
    for line in text.splitlines():
        lower = line.lower()
        if any(word in lower for word in sensitive_words):
            lines.append("[MASKED_SECRET_LINE]")
        else:
            lines.append(line)

    return "\n".join(lines)
