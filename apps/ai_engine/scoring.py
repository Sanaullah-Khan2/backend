"""
EduAIMS AI Risk Scoring Engine
Uses XGBoost ensemble to predict at-risk students.
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


def compute_features(student_id):
    """Extract feature vector for a single student from Supabase."""
    # 1. Attendance percentage (last 30 days)
    thirty_days_ago = (date.today() - timedelta(days=30)).isoformat()
    
    from eduaims.supabase_client import supabase
    
    attendance_res = supabase.table('attendance').select('status').eq('student_id', student_id).gte('date', thirty_days_ago).execute()
    att_data = attendance_res.data or []
    total_att = len(att_data)
    present_att = sum(1 for a in att_data if a.get('status') == 'present')
    late_att = sum(1 for a in att_data if a.get('status') == 'late')
    absent_count = sum(1 for a in att_data if a.get('status') == 'absent')
    
    attendance_pct = ((present_att + late_att * 0.5) / total_att * 100) if total_att > 0 else 100.0
    
    # 2. Grade average (all terms)
    grade_res = supabase.table('grades').select('score, total_score').eq('student_id', student_id).execute()
    grade_data = grade_res.data or []
    
    total_score_sum = sum(g.get('score', 0) or 0 for g in grade_data)
    total_max_sum = sum(g.get('total_score', 100) or 100 for g in grade_data)
    
    grade_avg = (float(total_score_sum) / float(total_max_sum) * 100) if total_max_sum > 0 else 50.0
    
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
    Uses the trained XGBoost model via risk_engine.
    Returns list of created RiskScore objects.
    """
    from apps.ai_engine.risk_engine import calculate_risk_score
    from eduaims.supabase_client import supabase
    
    # Fetch students from Supabase
    students_res = supabase.table('students').select('*').eq('is_active', True).execute()
    students = students_res.data or []
    
    if not students:
        return []
    
    results = []
    for student in students:
        student_id = student['id']
        features = compute_features(student_id)
        
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
        
        # Write to Supabase risk_scores table
        risk_data = {
            'student_id': student_id,
            'score': score,
            'risk_level': level.lower(),
            'attendance_pct': attendance_pct,
            'grade_avg': grade_avg,
            'assignments_missed': features['assignments_missed'],
            'top_factors': [reason]
        }
        
        # We can update if exists, or insert new. Let's try upsert or delete then insert.
        # But supabase doesn't have a direct upsert without a unique constraint easily known here.
        # We will insert new records.
        res = supabase.table('risk_scores').insert(risk_data).execute()
        if res.data:
            results.append(res.data[0])
    
    return results
