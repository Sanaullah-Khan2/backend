from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Report
from .serializers import ReportSerializer
from .nlg import generate_student_report
from apps.students.models import Student

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all().select_related('student', 'generated_by')
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='generate')
    def generate_report(self, request):
        student_id = request.data.get('student_id')
        if not student_id:
            return Response({"error": "student_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            student = Student.objects.get(_id=student_id)
        except Student.DoesNotExist:
            return Response({"error": "Student not found"}, status=status.HTTP_404_NOT_FOUND)
            
        text, risk_level = generate_student_report(student_id)
        
        report = Report.objects.create(
            student=student,
            generated_text=text,
            generated_by=request.user,
            risk_level_snapshot=risk_level
        )
        
        serializer = self.get_serializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='student/(?P<student_id>[^/.]+)')
    def student_reports(self, request, student_id=None):
        records = self.queryset.filter(student___id=student_id)
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)
