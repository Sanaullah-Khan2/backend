from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import AttendanceRecord
from .serializers import AttendanceRecordSerializer
from apps.students.models import Student
from datetime import datetime

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = AttendanceRecord.objects.all().order_by('-date')
    serializer_class = AttendanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='mark')
    def mark_attendance(self, request):
        date_str = request.data.get('date')
        subject_id = request.data.get('subject_id', '')
        records = request.data.get('records', [])
        
        if not date_str or not records:
            return Response({"error": "date and records are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        marked_by = request.user
        created_records = []
        
        for record_data in records:
            student_id = record_data.get('student_id')
            att_status = record_data.get('status')
            try:
                student = Student.objects.get(_id=student_id)
                # update_or_create to avoid duplicate entries
                record, created = AttendanceRecord.objects.update_or_create(
                    student=student,
                    date=date_str,
                    subject_id=subject_id,
                    defaults={'status': att_status, 'marked_by': marked_by}
                )
                created_records.append(AttendanceRecordSerializer(record).data)
            except Student.DoesNotExist:
                continue

        return Response({"message": "Attendance marked", "records": created_records}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='student/(?P<student_id>[^/.]+)')
    def student_attendance(self, request, student_id=None):
        records = AttendanceRecord.objects.filter(student___id=student_id).order_by('-date')
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='class/(?P<class_id>[^/.]+)/date/(?P<date_str>[^/.]+)')
    def class_attendance(self, request, class_id=None, date_str=None):
        students = Student.objects.filter(class_id=class_id)
        records = AttendanceRecord.objects.filter(student__in=students, date=date_str)
        record_map = {r.student_id: r for r in records}
        
        response_data = []
        for s in students:
            if s._id in record_map:
                response_data.append(AttendanceRecordSerializer(record_map[s._id]).data)
            else:
                response_data.append({
                    "student": s._id,
                    "student_name": s.full_name,
                    "student_registration_no": s.registration_no,
                    "status": None
                })
                
        return Response(response_data)
