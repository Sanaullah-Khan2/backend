from rest_framework import serializers
from .models import Fee

class FeeSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_registration_no = serializers.CharField(source='student.registration_no', read_only=True)
    student_class = serializers.CharField(source='student.class_id', read_only=True)

    class Meta:
        model = Fee
        fields = ('_id', 'student', 'student_name', 'student_registration_no', 'student_class', 
                  'title', 'amount', 'due_date', 'status', 'paid_date', 'created_at')
        read_only_fields = ('_id', 'created_at')
