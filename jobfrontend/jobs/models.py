from django.db import models


class AuditLog(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    username = models.CharField(max_length=120, blank=True, null=True)
    action = models.CharField(max_length=120)
    target = models.CharField(max_length=255, blank=True, null=True)

    safety_mode = models.CharField(max_length=40, default="READ_ONLY")
    status = models.CharField(max_length=40, default="ALLOWED")

    details = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.created_at} | {self.username} | {self.action} | {self.status}"

# Create your models here.
