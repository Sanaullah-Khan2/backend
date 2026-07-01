"""
URL configuration for eduaims project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from apps.reports import views as reports_views


def api_root(request):
    """Root endpoint — confirms the EduAIMS API is running."""
    return JsonResponse({
        "status": "ok",
        "message": "EduAIMS API is running.",
        "version": "1.0.0",
        "docs": "Use /api/ prefixed endpoints to interact with the system.",
        "portals": {
            "admin":   "/api/admin/",
            "auth":    "/api/auth/",
            "students":"/api/students/",
            "faculty": "/api/faculty/",
            "grades":  "/api/grades/",
            "ai":      "/api/ai/",
        }
    })


urlpatterns = [
    path('', api_root, name='api_root'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.auth_app.urls')),
    path('api/students/', include('apps.students.urls')),
    path('api/faculty/', include('apps.faculty.urls')),
    path('api/attendance/', include('apps.attendance.urls')),
    path('api/grades/', include('apps.grades.urls')),
    path('api/ai/', include('apps.ai_engine.urls')),
    path('api/interventions/', include('apps.interventions.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/finances/', include('apps.finances.urls')),
    path('api/audit/', include('apps.audit.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/assignments/', include('apps.assignments.urls')),
    path('api/admin/dashboard-stats/', reports_views.admin_dashboard_stats, name='admin_dashboard_stats'),
    path('api/admin/highlights/', reports_views.admin_highlights, name='admin_highlights'),
    path('api/announcements/', reports_views.announcements_list, name='announcements_list'),
]

