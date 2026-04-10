import uuid
from django.db import models
from django.conf import settings

class Student(models.Model):
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    registration_no = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    dob = models.DateField()
    class_id = models.CharField(max_length=50) 
    section = models.CharField(max_length=10)
    parent_contact = models.CharField(max_length=20)
    parent_email = models.EmailField()
    enrolled_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.full_name} ({self.registration_no})"
