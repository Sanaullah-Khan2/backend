import uuid
from django.db import models
from django.conf import settings
from apps.students.models import Student

class Intervention(models.Model):
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in-progress', 'In Progress'),
        ('resolved', 'Resolved')
    )
    
    TYPE_CHOICES = (
        ('parent-contact', 'Parent Contacted'),
        ('counseling', 'Counseling Session'),
        ('tutoring', 'Extra Tutoring'),
        ('meeting', 'Teacher-Student Meeting'),
        ('other', 'Other')
    )
    
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='interventions')
    logged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='logged_interventions')
    intervention_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.full_name} - {self.get_intervention_type_display()} ({self.status})"
