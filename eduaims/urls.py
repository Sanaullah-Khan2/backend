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

urlpatterns = [
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
]
