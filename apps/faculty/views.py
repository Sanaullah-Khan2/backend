from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import Faculty
from .serializers import FacultySerializer

class FacultyViewSet(viewsets.ModelViewSet):
    queryset = Faculty.objects.all().order_by('-joined_date')
    serializer_class = FacultySerializer
    permission_classes = [permissions.IsAuthenticated]

# ── TEACHER PORTAL MOCK APIS ──────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def teacher_dashboard_kpis(request):
    """Return high-level KPIs for the Teacher Dashboard"""
    data = {
        "total_classes": 3,
        "total_students": 115,
        "assignments_pending": 12,
        "students_at_risk": 5
    }
    return Response({"success": True, "data": data})

@api_view(['GET'])
@permission_classes([AllowAny])
def teacher_classes(request):
    """Return classes assigned to the teacher"""
    data = [
        {"id": "c1", "name": "9-A Mathematics", "students": 38, "average": 78},
        {"id": "c2", "name": "10-A Mathematics", "students": 42, "average": 81},
        {"id": "c3", "name": "11-B Physics", "students": 35, "average": 74}
    ]
    return Response({"success": True, "data": data})

@api_view(['GET'])
@permission_classes([AllowAny])
def teacher_alerts(request):
    """Return students at risk in the teacher's classes"""
    data = [
        {"id": "s1", "name": "Ali Hassan", "class": "9-A Mathematics", "score": 75, "level": "red", "reason": "Consistent grade drop"},
        {"id": "s2", "name": "Sara Ahmed", "class": "10-A Mathematics", "score": 48, "level": "yellow", "reason": "Low attendance"},
        {"id": "s3", "name": "Bilal Khan", "class": "9-A Mathematics", "score": 72, "level": "red", "reason": "Failed mid-term"}
    ]
    return Response({"success": True, "data": data})
