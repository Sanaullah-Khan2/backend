from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InterventionViewSet

router = DefaultRouter()
router.register(r'', InterventionViewSet, basename='intervention')

urlpatterns = [
    path('', include(router.urls)),
]
