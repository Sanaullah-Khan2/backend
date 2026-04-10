from rest_framework import serializers
from .models import Intervention

class InterventionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_class = serializers.CharField(source='student.class_id', read_only=True)
    logged_by_name = serializers.CharField(source='logged_by.name', read_only=True)
    intervention_type_display = serializers.CharField(source='get_intervention_type_display', read_only=True)

    class Meta:
        model = Intervention
        fields = ('_id', 'student', 'student_name', 'student_class', 'logged_by', 'logged_by_name', 
                  'intervention_type', 'intervention_type_display', 'status', 'notes', 'created_at', 'updated_at')
        read_only_fields = ('_id', 'logged_by', 'created_at', 'updated_at')
