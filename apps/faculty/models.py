import uuid
from django.db import models
from django.conf import settings

class Faculty(models.Model):
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='faculty_profile')
    employee_id = models.CharField(max_length=50, unique=True, blank=True)
    full_name = models.CharField(max_length=255)
    subject_specialization = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20)
    classes_assigned = models.TextField(blank=True, help_text="Comma separated class IDs")
    joined_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.employee_id:
            self.employee_id = f"EMP-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.subject_specialization})"
