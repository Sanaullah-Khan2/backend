from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportViewSet
from . import views

router = DefaultRouter()
router.register(r'', ReportViewSet, basename='report')

urlpatterns = [
    path('admin-dashboard/', views.admin_dashboard_kpis, name='admin_dashboard_kpis'),
    path('', include(router.urls)),
]
