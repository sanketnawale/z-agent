SAFE_READ_ACTIONS = {
    "VIEW_JOBS",
    "VIEW_SPOOL",
    "VIEW_DATASET",
    "VIEW_USS",
    "AI_EXPLAIN",
}

RISKY_ACTIONS = {
    "SUBMIT_JCL",
    "CANCEL_JOB",
    "DELETE_DATASET",
    "WRITE_USS_FILE",
}


def get_safety_mode(request):
    return request.session.get("safety_mode", "READ_ONLY")


def is_action_allowed(action, safety_mode):
    if action in SAFE_READ_ACTIONS:
        return True

    if safety_mode == "READ_ONLY":
        return False

    if safety_mode == "APPROVAL_REQUIRED":
        return False

    if safety_mode == "EXECUTE":
        return True

    return False


def mask_secret(value):
    if not value:
        return value
    if len(value) <= 4:
        return "****"
    return value[:2] + "****" + value[-2:]
