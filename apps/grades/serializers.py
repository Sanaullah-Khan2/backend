from rest_framework import serializers
from .models import Grade

class GradeSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_registration_no = serializers.CharField(source='student.registration_no', read_only=True)

    class Meta:
        model = Grade
        fields = ('_id', 'student', 'student_name', 'student_registration_no', 'subject_id', 'term', 'score', 'total_score', 'recorded_by', 'recorded_date')
        read_only_fields = ('_id', 'recorded_by', 'recorded_date')
