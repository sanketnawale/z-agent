from .models import AuditLog
from .safety import get_safety_mode


def write_audit_log(request, action, target="", status="ALLOWED", details=""):
    username = request.session.get("zos_user", "unknown")
    safety_mode = get_safety_mode(request)

    AuditLog.objects.create(
        username=username,
        action=action,
        target=target,
        safety_mode=safety_mode,
        status=status,
        details=details,
    )
