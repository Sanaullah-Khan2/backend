import uuid
from django.db import models
from apps.students.models import Student

class RiskScore(models.Model):
    RISK_CHOICES = (
        ('green', 'Safe'),
        ('yellow', 'Moderate Risk'),
        ('red', 'High Risk')
    )
    
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='risk_scores')
    score = models.FloatField(help_text="0-100 probability of being at-risk")
    risk_level = models.CharField(max_length=20, choices=RISK_CHOICES)
    
    # Feature snapshot at time of scoring
    attendance_pct = models.FloatField(default=0)
    grade_avg = models.FloatField(default=0)
    assignments_missed = models.IntegerField(default=0)
    
    # Top contributing factors from the model
    top_factors = models.JSONField(default=list, blank=True)
    
    scored_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-scored_at']
    
    def __str__(self):
        return f"{self.student.full_name}: {self.risk_level} ({self.score}%)"
