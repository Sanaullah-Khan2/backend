from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Student
from .serializers import StudentSerializer

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all().order_by('-enrolled_date')
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=['post'], url_path='bulk-import')
    def bulk_import(self, request):
        # Placeholder for bulk CSV import logic
        return Response({"status": "Bulk import placeholder"}, status=200)

# ── STUDENT PORTAL ENDPOINTS ─────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def student_dashboard_kpis(request):
    """Return KPIs for the student dashboard (mock data)"""
    data = {
        "grade_average": 78,
        "attendance_pct": 82,
        "assignments_pending": 3,
        "rank_in_class": 12,
        "subjects_total": 7
    }
    return Response({"success": True, "data": data})

@api_view(['GET'])
@permission_classes([AllowAny])
def student_performance(request):
    """Return student's recent grade history per subject"""
    data = [
        {"subject": "Mathematics",   "monthly": 72, "midterm": 68, "final": 75},
        {"subject": "Physics",        "monthly": 80, "midterm": 76, "final": 82},
        {"subject": "Chemistry",      "monthly": 65, "midterm": 70, "final": 69},
        {"subject": "English",        "monthly": 88, "midterm": 85, "final": 90},
        {"subject": "Computer Sci",   "monthly": 92, "midterm": 88, "final": 95},
        {"subject": "Urdu",           "monthly": 70, "midterm": 73, "final": 71},
        {"subject": "Islamiyat",      "monthly": 78, "midterm": 80, "final": 82},
    ]
    return Response({"success": True, "data": data})

@api_view(['GET'])
@permission_classes([AllowAny])
def student_ai_tips(request):
    """Return personalized AI study tips based on performance"""
    data = [
        {
            "type": "warning",
            "subject": "Chemistry",
            "tip": "Your Chemistry scores have been below 70. Consider reviewing Chapter 5 and 6 exercises."
        },
        {
            "type": "success",
            "subject": "Computer Science",
            "tip": "Excellent performance in Computer Science! You are ranked in the top 10% of your class."
        },
        {
            "type": "info",
            "subject": "Attendance",
            "tip": "Your attendance is 82%. Try to maintain above 85% to avoid academic penalties."
        },
        {
            "type": "info",
            "subject": "Mathematics",
            "tip": "Practice more algebra problems. Your mid-term score dropped from last month."
        }
    ]
    return Response({"success": True, "data": data})

# ── PARENT PORTAL ENDPOINTS ──────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def parent_child_overview(request):
    """Return the child overview for the parent (mock data)"""
    data = {
        "child_name": "Ali Hassan",
        "class_name": "10-A",
        "roll_no": "10A-15",
        "grade_average": 74,
        "attendance_pct": 80,
        "risk_level": "yellow",
        "risk_reason": "Attendance dropped below 82% this month",
        "teacher_name": "Mr. Asad Khan"
    }
    return Response({"success": True, "data": data})

@api_view(['GET'])
@permission_classes([AllowAny])
def parent_child_grades(request):
    """Return child's most recent grades per subject"""
    data = [
        {"subject": "Mathematics",   "monthly": 70, "midterm": 65, "final": 72},
        {"subject": "Physics",        "monthly": 78, "midterm": 74, "final": 79},
        {"subject": "Chemistry",      "monthly": 60, "midterm": 64, "final": 66},
        {"subject": "English",        "monthly": 85, "midterm": 82, "final": 88},
        {"subject": "Computer Sci",   "monthly": 90, "midterm": 87, "final": 92},
        {"subject": "Urdu",           "monthly": 68, "midterm": 72, "final": 70},
        {"subject": "Islamiyat",      "monthly": 75, "midterm": 78, "final": 80},
    ]
    return Response({"success": True, "data": data})

@api_view(['GET'])
@permission_classes([AllowAny])
def parent_child_alerts(request):
    """Return AI alerts for the parent's child"""
    data = [
        {
            "type": "warning",
            "date": "2024-03-28",
            "message": "Ali's Mathematics score dropped from 78 to 65 this month. Consider tutoring support."
        },
        {
            "type": "info",
            "date": "2024-03-25",
            "message": "Attendance this month is 80%, slightly below the 85% recommended threshold."
        },
        {
            "type": "success",
            "date": "2024-03-20",
            "message": "Ali scored 92% in Computer Science Final — top performer in class!"
        }
    ]
    return Response({"success": True, "data": data})

@api_view(['GET'])
@permission_classes([AllowAny])
def parent_narrative_report(request):
    """Return a plain-text narrative report for the parent"""
    data = {
        "generated_at": "2024-03-28",
        "report": (
            "Ali Hassan is currently performing at an average level across all subjects with an overall grade average "
            "of 74%. His strongest subject this term is Computer Science (92%) where he consistently ranks in the top "
            "10% of the class. Areas requiring attention include Mathematics and Chemistry, where scores have shown a "
            "slight downward trend this month. "
            "His attendance currently stands at 80%, which is slightly below the recommended 85% threshold. Consistent "
            "class attendance is strongly encouraged to prevent further academic risk. "
            "The AI Engine has flagged Ali as a Yellow Risk student this month, primarily due to his attendance and "
            "Math performance. We recommend reviewing study habits and attending extra help sessions if available."
        )
    }
    return Response({"success": True, "data": data})
