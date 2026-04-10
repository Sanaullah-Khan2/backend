from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Fee
from .serializers import FeeSerializer
from apps.students.models import Student

class FeeViewSet(viewsets.ModelViewSet):
    queryset = Fee.objects.all().select_related('student')
    serializer_class = FeeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Auto-update status to overdue if due_date passed and still pending
        today = timezone.now().date()
        Fee.objects.filter(status='pending', due_date__lt=today).update(status='overdue')
        return super().get_queryset()

    @action(detail=True, methods=['post'], url_path='pay')
    def mark_paid(self, request, pk=None):
        try:
            fee = self.get_object()
        except Exception:
            return Response({"error": "Fee not found"}, status=status.HTTP_404_NOT_FOUND)
            
        if fee.status == 'paid':
            return Response({"error": "Fee is already paid"}, status=status.HTTP_400_BAD_REQUEST)
            
        fee.status = 'paid'
        fee.paid_date = timezone.now().date()
        fee.save()
        
        serializer = self.get_serializer(fee)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='student/(?P<student_id>[^/.]+)')
    def student_fees(self, request, student_id=None):
        records = self.get_queryset().filter(student___id=student_id)
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)
