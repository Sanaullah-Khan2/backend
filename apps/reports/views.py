from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from .models import Report
from .serializers import ReportSerializer
from .nlg import generate_student_report
from apps.students.models import Student
from eduaims.supabase_client import supabase
from django.utils import timezone

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_dashboard_kpis(request):
    try:
        # Get total students
        student_res = supabase.table('students').select('id', count='exact').execute()
        total_students = student_res.count or 0
        
        # Get fees collection
        fees_res = supabase.table('fees').select('*').execute()
        fees = fees_res.data or []
        total_collected = sum(f['amount_paid'] or 0 for f in fees if f['status'] == 'paid')
        total_expected = sum(f['amount_due'] or 0 for f in fees)
        collection_rate = (total_collected / total_expected * 100) if total_expected > 0 else 0
        
        # Get at risk students
        risk_res = supabase.table('ai_scores').select('id', count='exact').eq('risk_level', 'red').execute()
        at_risk = risk_res.count or 0
        
        # Get recent activity
        audit_res = supabase.table('audit_log').select('*').order('created_at', desc=True).limit(5).execute()
        
        kpis = {
            'total_students': total_students,
            'students_at_risk': at_risk,
            'collection_rate': f"{round(collection_rate, 1)}%",
            'avg_attendance': "85.0%" # Attendance table logic would go here
        }
        
        return Response({"success": True, "kpis": kpis, "recent_activity": audit_res.data})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)

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
