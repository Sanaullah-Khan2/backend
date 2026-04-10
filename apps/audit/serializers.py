from rest_framework import serializers
from .models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True, default='System')
    role = serializers.CharField(source='user.role', read_only=True, default='unknown')

    class Meta:
        model = AuditLog
        fields = ('_id', 'user', 'user_name', 'role', 'action', 'model_name', 'details', 'timestamp')
