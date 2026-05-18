from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FacultyViewSet
from . import views

router = DefaultRouter()
router.register(r'', FacultyViewSet, basename='faculty')

urlpatterns = [
    path('teacher/dashboard-kpis/', views.teacher_dashboard_kpis, name='teacher_dashboard_kpis'),
    path('teacher/classes/', views.teacher_classes, name='teacher_classes'),
    path('teacher/alerts/', views.teacher_alerts, name='teacher_alerts'),
    path('teacher/highlights/', views.teacher_highlights, name='teacher_highlights'),
    path('', include(router.urls)),
]
