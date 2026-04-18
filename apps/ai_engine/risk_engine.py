import pickle
import os
import numpy as np

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    'model', 'risk_model.pkl'
)

def load_model():
    try:
        with open(MODEL_PATH, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return None

def calculate_risk_score(attendance_pct, grade_avg, grade_trend,
                          fee_default=0, behavior_count=0):
    """
    Calculate risk score using trained Random Forest model.
    Falls back to rule-based scoring if model not found.
    Returns: score (0-100), level (green/yellow/red), reason (string)
    """
    model_data = load_model()

    if model_data:
        try:
            model   = model_data['model']
            # Simple features that match what we have
            features = np.array([[
                attendance_pct,
                grade_avg,
                grade_trend,
                fee_default,
                behavior_count
            ]])
            proba = model.predict_proba(features)[0]
            # proba[0]=Graduate(safe), proba[1]=Enrolled(watch), proba[2]=Dropout(risk)
            # Map to 0-100 score
            classes = model_data.get('classes', [])
            dropout_idx  = list(classes).index('Dropout')  if 'Dropout'  in classes else 2
            enrolled_idx = list(classes).index('Enrolled') if 'Enrolled' in classes else 1
            score = round(proba[dropout_idx] * 100 + proba[enrolled_idx] * 40)
            score = min(score, 100)
        except Exception:
            score = _rule_based_score(attendance_pct, grade_avg, grade_trend)
    else:
        score = _rule_based_score(attendance_pct, grade_avg, grade_trend)

    # Determine level
    if score >= 70:
        level = 'red'
    elif score >= 40:
        level = 'yellow'
    else:
        level = 'green'

    # Generate reason
    if attendance_pct < 75 and grade_avg < 50:
        reason = f'Low attendance ({attendance_pct:.0f}%) and low grades ({grade_avg:.0f}%)'
    elif attendance_pct < 75:
        reason = f'Low attendance ({attendance_pct:.0f}%)'
    elif grade_avg < 50:
        reason = f'Low grade average ({grade_avg:.0f}%)'
    elif grade_trend < -15:
        reason = f'Grade dropped {abs(grade_trend):.0f}% from last month'
    elif fee_default:
        reason = 'Fees unpaid for over 30 days'
    else:
        reason = 'Student performing well'

    return score, level, reason

def _rule_based_score(attendance_pct, grade_avg, grade_trend):
    score = 0
    if attendance_pct < 75:  score += 40
    if grade_avg < 50:        score += 35
    if grade_trend < -15:     score += 25
    return min(score, 100)
