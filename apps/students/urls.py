from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentViewSet
from . import views

router = DefaultRouter()
router.register(r'', StudentViewSet, basename='student')

urlpatterns = [
    path('portal/dashboard-kpis/', views.student_dashboard_kpis, name='student_dashboard_kpis'),
    path('portal/performance/', views.student_performance, name='student_performance'),
    path('portal/ai-tips/', views.student_ai_tips, name='student_ai_tips'),
    path('parent/child-overview/', views.parent_child_overview, name='parent_child_overview'),
    path('parent/child-grades/', views.parent_child_grades, name='parent_child_grades'),
    path('parent/child-alerts/', views.parent_child_alerts, name='parent_child_alerts'),
    path('parent/narrative-report/', views.parent_narrative_report, name='parent_narrative_report'),
    path('', include(router.urls)),
]
