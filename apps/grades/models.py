import uuid
from django.db import models
from django.conf import settings
from apps.students.models import Student

class Grade(models.Model):
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grades')
    subject_id = models.CharField(max_length=50)
    term = models.CharField(max_length=50) # e.g. "Midterm 1", "Finals"
    score = models.DecimalField(max_digits=5, decimal_places=2)
    total_score = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    recorded_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('student', 'subject_id', 'term')

    def __str__(self):
        return f"{self.student.full_name} - {self.subject_id} - {self.term}: {self.score}/{self.total_score}"
