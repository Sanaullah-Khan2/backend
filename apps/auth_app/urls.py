from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from .views import CustomTokenObtainPairView, UserMeView

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', UserMeView.as_view(), name='user_me'),
    
    path('settings/audit-log/', views.audit_log, name='audit-log'),
    path('settings/users/', views.list_users, name='list-users'),
    path('settings/users/<str:user_id>/deactivate/', views.deactivate_user, name='deactivate-user'),
    path('settings/school-profile/', views.school_profile, name='school-profile'),
    path('create-user/', views.create_user_view, name='create-user'),
    path('create-admin/', views.create_admin_view, name='create-admin'),
    path('register/', views.register_view, name='register'),
]
