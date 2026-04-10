from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Grade
from .serializers import GradeSerializer
from apps.students.models import Student

class GradeViewSet(viewsets.ModelViewSet):
    queryset = Grade.objects.all().order_by('-recorded_date')
    serializer_class = GradeSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='bulk-mark')
    def bulk_mark(self, request):
        subject_id = request.data.get('subject_id')
        term = request.data.get('term')
        records = request.data.get('records', [])
        
        if not subject_id or not term or not records:
            return Response({"error": "subject_id, term, and records are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        recorded_by = request.user
        created_records = []
        
        for record_data in records:
            student_id = record_data.get('student_id')
            score = record_data.get('score')
            total_score = record_data.get('total_score', 100.00)
            
            try:
                student = Student.objects.get(_id=student_id)
                # update_or_create to avoid duplicate entries
                record, created = Grade.objects.update_or_create(
                    student=student,
                    subject_id=subject_id,
                    term=term,
                    defaults={'score': score, 'total_score': total_score, 'recorded_by': recorded_by}
                )
                created_records.append(GradeSerializer(record).data)
            except Student.DoesNotExist:
                continue

        return Response({"message": "Grades saved", "records": created_records}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='student/(?P<student_id>[^/.]+)')
    def student_grades(self, request, student_id=None):
        records = Grade.objects.filter(student___id=student_id).order_by('-recorded_date')
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='class/(?P<class_id>[^/.]+)/subject/(?P<subject_id>[^/.]+)/term/(?P<term>[^/.]+)')
    def class_grades(self, request, class_id=None, subject_id=None, term=None):
        students = Student.objects.filter(class_id=class_id)
        records = Grade.objects.filter(student__in=students, subject_id=subject_id, term=term)
        record_map = {r.student_id: r for r in records}
        
        response_data = []
        for s in students:
            if s._id in record_map:
                response_data.append(GradeSerializer(record_map[s._id]).data)
            else:
                response_data.append({
                    "student": s._id,
                    "student_name": s.full_name,
                    "student_registration_no": s.registration_no,
                    "score": "",
                    "total_score": 100.00
                })
                
        return Response(response_data)
