import uuid
from django.db import models
from django.conf import settings
from apps.students.models import Student

class Report(models.Model):
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='reports')
    generated_text = models.TextField()
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Snapshot factors at generation time for auditing purposes
    risk_level_snapshot = models.CharField(max_length=20, default='green')
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report for {self.student.full_name} generated on {self.created_at.strftime('%Y-%m-%d')}"
