from rest_framework import serializers
from .models import RiskScore

class RiskScoreSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_registration_no = serializers.CharField(source='student.registration_no', read_only=True)
    student_class = serializers.CharField(source='student.class_id', read_only=True)

    class Meta:
        model = RiskScore
        fields = ('_id', 'student', 'student_name', 'student_registration_no', 'student_class',
                  'score', 'risk_level', 'attendance_pct', 'grade_avg', 
                  'assignments_missed', 'top_factors', 'scored_at')
