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
    path("explain-spool/", views.explain_spool_ai, name="explain_spool_ai"),
    path("submit-jcl/", views.submit_jcl, name="submit_jcl"),
    path("audit/", views.audit_logs, name="audit_logs"),
    path("safety/", views.safety_settings_view, name="safety_settings"),
    path("api/devops/job-summary", views.devops_job_summary, name="devops_job_summary"),
    path("api/devops/incident-summary", views.devops_incident_summary, name="devops_incident_summary"),
    path("api/devops/notify", views.devops_notify, name="devops_notify"),
    path("api/performance/insights", views.performance_insights_api, name="performance_insights_api"),
    path("performance/", views.performance_insights_view, name="performance_insights"),
]