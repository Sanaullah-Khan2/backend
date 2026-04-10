from rest_framework import serializers
from .models import Report

class ReportSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    generated_by_name = serializers.CharField(source='generated_by.name', read_only=True)

    class Meta:
        model = Report
        fields = ('_id', 'student', 'student_name', 'generated_text', 'generated_by', 'generated_by_name', 'risk_level_snapshot', 'created_at')
        read_only_fields = ('_id', 'generated_by', 'created_at')
