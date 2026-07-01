from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentViewSet
from . import views
from . import parent_views

router = DefaultRouter()
router.register(r'', StudentViewSet, basename='student')

urlpatterns = [
    path('portal/dashboard-kpis/', views.student_dashboard_kpis, name='student_dashboard_kpis'),
    path('portal/performance/', views.student_performance, name='student_performance'),
    path('portal/ai-tips/', views.student_ai_tips, name='student_ai_tips'),
    path('portal/attendance/', views.student_attendance, name='student_attendance'),
    path('parent/child-overview/', parent_views.child_overview, name='parent_child_overview'),
    path('parent/child-grades/', views.parent_child_grades, name='parent_child_grades'),
    path('parent/child-alerts/', views.parent_child_alerts, name='parent_child_alerts'),
    path('parent/attendance/', parent_views.attendance, name='parent_attendance'),
    path('parent/monthly-report/', parent_views.monthly_report, name='parent_monthly_report'),
    path('parent/fees/', parent_views.fees, name='parent_fees'),
    path('enroll/', views.enroll_student, name='enroll_student'),
    path('enrollment/request/', views.request_enrollment, name='request_enrollment'),
    path('enrollment/requests/', views.get_enrollment_requests, name='get_enrollment_requests'),
    path('enrollment/requests/<str:request_id>/approve/', views.approve_enrollment, name='approve_enrollment'),
    path('enrollment/requests/<str:request_id>/reject/', views.reject_enrollment, name='reject_enrollment'),
    path('', include(router.urls)),
]
