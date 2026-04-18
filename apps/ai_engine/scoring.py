"""
EduAIMS AI Risk Scoring Engine
Uses Random Forest + Logistic Regression ensemble to predict at-risk students.
Features: attendance %, grade average, assignments missed.
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from django.db.models import Avg, Count, Q
from datetime import timedelta, date

from apps.students.models import Student
from apps.attendance.models import AttendanceRecord
from apps.grades.models import Grade
from apps.ai_engine.models import RiskScore


def compute_features(student):
    """Extract feature vector for a single student."""
    # 1. Attendance percentage (last 30 days)
    thirty_days_ago = date.today() - timedelta(days=30)
    attendance_qs = AttendanceRecord.objects.filter(
        student=student,
        date__gte=thirty_days_ago
    )
    total_att = attendance_qs.count()
    present_att = attendance_qs.filter(status='present').count()
    late_att = attendance_qs.filter(status='late').count()
    attendance_pct = ((present_att + late_att * 0.5) / total_att * 100) if total_att > 0 else 100.0
    
    # 2. Grade average (all terms)
    grade_agg = Grade.objects.filter(student=student).aggregate(
        avg_score=Avg('score'),
        avg_total=Avg('total_score')
    )
    avg_score = grade_agg['avg_score'] or 0
    avg_total = grade_agg['avg_total'] or 100
    grade_avg = (float(avg_score) / float(avg_total) * 100) if avg_total > 0 else 50.0
    
    # 3. Absent days count (proxy for assignments missed)
    absent_count = attendance_qs.filter(status='absent').count()
    
    return {
        'attendance_pct': round(attendance_pct, 2),
        'grade_avg': round(grade_avg, 2),
        'assignments_missed': absent_count,
    }


def classify_risk(probability):
    """Convert probability to risk level."""
    if probability >= 70:
        return 'red'
    elif probability >= 40:
        return 'yellow'
    else:
        return 'green'


def get_top_factors(features):
    """Determine contributing factors from feature values."""
    factors = []
    if features['attendance_pct'] < 75:
        factors.append(f"Low attendance ({features['attendance_pct']}%)")
    if features['grade_avg'] < 50:
        factors.append(f"Below-average grades ({features['grade_avg']}%)")
    if features['assignments_missed'] >= 3:
        factors.append(f"Frequent absences ({features['assignments_missed']} in 30 days)")
    if not factors:
        factors.append("No significant risk factors detected")
    return factors


def build_training_data():
    """
    Build synthetic training data based on real student features.
    In production, this would use historical labeled data.
    For the MVP, we generate labels heuristically.
    """
    students = Student.objects.filter(is_active=True)
    X, y = [], []
    
    for student in students:
        features = compute_features(student)
        feature_vector = [
            features['attendance_pct'],
            features['grade_avg'],
            features['assignments_missed']
        ]
        X.append(feature_vector)
        
        # Heuristic labeling for MVP
        risk_score = 0
        if features['attendance_pct'] < 75:
            risk_score += 40
        if features['grade_avg'] < 50:
            risk_score += 35
        if features['assignments_missed'] >= 3:
            risk_score += 25
        y.append(1 if risk_score >= 50 else 0)
    
    return np.array(X) if X else np.array([]).reshape(0, 3), np.array(y)


def score_all_students():
    """
    Run the AI scoring engine across all active students.
    Uses the trained Random Forest model via risk_engine.
    Returns list of created RiskScore objects.
    """
    from apps.ai_engine.risk_engine import calculate_risk_score
    
    students = Student.objects.filter(is_active=True)
    
    if students.count() == 0:
        return []
    
    results = []
    for student in students:
        features = compute_features(student)
        
        # Map our 3 basic features to the 5 features required by the enhanced ML model
        # Defaulting grade_trend, fee_default, and behavior_count
        attendance_pct = features['attendance_pct']
        grade_avg = features['grade_avg']
        grade_trend = 0  # Default to 0 for MVP
        fee_default = 0  # Default to 0 for MVP
        behavior_count = features['assignments_missed']  # Using missed assignments as behavioral proxy
        
        # Call the standalone AI model engine
        score, level, reason = calculate_risk_score(
            attendance_pct=attendance_pct,
            grade_avg=grade_avg,
            grade_trend=grade_trend,
            fee_default=fee_default,
            behavior_count=behavior_count
        )
        
        risk_score = RiskScore.objects.create(
            student=student,
            score=score,
            risk_level=level.lower(),
            attendance_pct=attendance_pct,
            grade_avg=grade_avg,
            assignments_missed=features['assignments_missed'],
            top_factors=[reason]  # The ML model returns a single descriptive string
        )
        results.append(risk_score)
    
    return results
