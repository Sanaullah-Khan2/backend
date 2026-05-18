import pickle
import os
import numpy as np

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    'model', 'xgb_risk_model.pkl'
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
    Calculate risk score using trained XGBoost model.
    Falls back to rule-based scoring if model not found.
    Returns: score (0-100), level (green/yellow/red), reason (string)
    """
    model_data = load_model()

    if model_data:
        try:
            model = model_data['model']
            # Map the 5 features into the 15 features expected by the new XGBoost model
            features = np.array([[
                0,                               # unregistered
                max(0, 10 - behavior_count),     # num_submitted
                min(100, grade_avg + 10),        # max_score
                10,                              # num_assessments
                grade_avg,                       # avg_score
                attendance_pct * 0.9,            # active_days
                max(0, grade_avg - 10),          # min_score
                10.0,                            # std_score
                attendance_pct * 10,             # total_clicks
                5.0,                             # avg_clicks_day
                60,                              # studied_credits
                behavior_count,                  # num_failed_assess
                0,                               # num_of_prev_attempts
                5,                               # imd_band_enc
                2                                # highest_education_enc
            ]])
            
            proba = model.predict_proba(features)[0]
            classes = list(model.classes_)
            
            green_idx = classes.index('green') if 'green' in classes else 0
            yellow_idx = classes.index('yellow') if 'yellow' in classes else 1
            red_idx = classes.index('red') if 'red' in classes else 2
            
            # Map to 0-100 score
            score = round(proba[red_idx] * 100 + proba[yellow_idx] * 50)
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
