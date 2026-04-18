import pickle
import os
import numpy as np

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    'model', 'risk_model.pkl'
)

def load_model():
    with open(MODEL_PATH, 'rb') as f:
        return pickle.load(f)

def test_single_student(name, attendance_pct, grade_avg, grade_trend, fee_default=0, behavior_count=0):
    model_data = load_model()
    model      = model_data['model']
    classes    = model_data['classes']

    features = np.array([[attendance_pct, grade_avg, grade_trend, fee_default, behavior_count]])

    proba = model.predict_proba(features)[0]

    dropout_idx  = list(classes).index('Dropout')  if 'Dropout'  in classes else 2
    enrolled_idx = list(classes).index('Enrolled') if 'Enrolled' in classes else 1

    score = round(proba[dropout_idx] * 100 + proba[enrolled_idx] * 40)
    score = min(score, 100)

    if score >= 70:
        level = 'RED   (At Risk)'
    elif score >= 40:
        level = 'YELLOW (Watch)'
    else:
        level = 'GREEN  (Safe)'

    if attendance_pct < 75 and grade_avg < 50:
        reason = f'Low attendance ({attendance_pct:.0f}%) and low grades ({grade_avg:.0f}%)'
    elif attendance_pct < 75:
        reason = f'Low attendance ({attendance_pct:.0f}%)'
    elif grade_avg < 50:
        reason = f'Low grade average ({grade_avg:.0f}%)'
    elif grade_trend < -15:
        reason = f'Grade dropped {abs(grade_trend):.0f}% from last month'
    else:
        reason = 'Student performing well'

    print(f"Student : {name}")
    print(f"Score   : {score}/100")
    print(f"Level   : {level}")
    print(f"Reason  : {reason}")
    print(f"Att%    : {attendance_pct}%  |  Grade: {grade_avg}%  |  Trend: {grade_trend:+.0f}%")
    print("-" * 55)

print("=" * 55)
print("   EduAIMS AI Risk Model — Test Results")
print("=" * 55)
print()

# Test Case 1 — Good student
test_single_student(
    name           = "Ali Hassan (Good Student)",
    attendance_pct = 92,
    grade_avg      = 78,
    grade_trend    = +5,
    fee_default    = 0,
    behavior_count = 0
)

# Test Case 2 — Watch student
test_single_student(
    name           = "Sara Khan (Needs Attention)",
    attendance_pct = 68,
    grade_avg      = 62,
    grade_trend    = -8,
    fee_default    = 0,
    behavior_count = 1
)

# Test Case 3 — At risk student
test_single_student(
    name           = "Ahmed Raza (At Risk)",
    attendance_pct = 52,
    grade_avg      = 38,
    grade_trend    = -22,
    fee_default    = 1,
    behavior_count = 4
)

# Test Case 4 — Average student
test_single_student(
    name           = "Fatima Malik (Average)",
    attendance_pct = 80,
    grade_avg      = 55,
    grade_trend    = -5,
    fee_default    = 0,
    behavior_count = 0
)

# Test Case 5 — Border case
test_single_student(
    name           = "Usman Sheikh (Border Case)",
    attendance_pct = 74,
    grade_avg      = 51,
    grade_trend    = -14,
    fee_default    = 0,
    behavior_count = 2
)

print()
print("=" * 55)
print("Test complete!")
print("GREEN  = score 0-39   (Student is safe)")
print("YELLOW = score 40-69  (Needs monitoring)")
print("RED    = score 70-100 (Immediate action)")
print("=" * 55)
