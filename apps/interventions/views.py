from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Intervention
from .serializers import InterventionSerializer
from apps.students.models import Student

class InterventionViewSet(viewsets.ModelViewSet):
    queryset = Intervention.objects.all().select_related('student', 'logged_by')
    serializer_class = InterventionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(logged_by=self.request.user)

    @action(detail=False, methods=['get'], url_path='student/(?P<student_id>[^/.]+)')
    def student_history(self, request, student_id=None):
        records = self.queryset.filter(student___id=student_id)
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)
