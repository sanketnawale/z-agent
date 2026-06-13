from .models import AuditLog
from .safety import get_safety_mode, mask_text


def write_audit_log(request, action, target="", status="ALLOWED", details=""):
    profile = request.session.get("zowe_profile", {})
    username = profile.get("user", "unknown")
    safety_mode = get_safety_mode(request)

    AuditLog.objects.create(
        username=username,
        action=action,
        target=mask_text(target),
        safety_mode=safety_mode,
        status=status,
        details=mask_text(details),
    )
