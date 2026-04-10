from rest_framework import serializers
from .models import AttendanceRecord

class AttendanceRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_registration_no = serializers.CharField(source='student.registration_no', read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = ('_id', 'student', 'student_name', 'student_registration_no', 'date', 'status', 'subject_id', 'marked_by', 'created_at')
        read_only_fields = ('_id', 'marked_by', 'created_at')
