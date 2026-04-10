from django.urls import path
from . import views

urlpatterns = [
    path('send-email/', views.send_email, name='send_email'),
    path('send-sms/', views.send_sms, name='send_sms'),
    path('send-bulk-alert/', views.send_bulk_alert, name='send_bulk_alert'),
    path('log/', views.notification_log, name='notification_log'),
]
