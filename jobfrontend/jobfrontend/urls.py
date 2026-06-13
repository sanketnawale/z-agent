from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path
from jobs import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", lambda request: redirect("job_list"), name="home"),

    path("jobs/", views.job_list, name="job_list"),
    path("jobs/<str:jobid>/spool/", views.view_spool, name="view_spool"),
    path("uss/", views.uss_browser, name="uss_browser"),
    path("setup/", views.setup_view, name="setup"),
    path("logout/", views.logout_view, name="logout"),
    path("ai-settings/", views.ai_settings_view, name="ai_settings"),
    path("send_spool/", views.send_spool_to_ollama, name="send_spool"),
    path("explorer/", views.explorer, name="explorer"),
    path("explorer/member/<path:dataset_name>/<str:member_name>/", views.member_detail, name="member_detail"),
    path("explainer/member/", views.explain_member, name="explain_member"),
    path("submit-jcl/", views.submit_jcl, name="submit_jcl"),
    path("audit/", views.audit_logs, name="audit_logs"),
    path("safety/", views.safety_settings_view, name="safety_settings"),
]