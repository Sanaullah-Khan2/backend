from apps.students.models import Student
from apps.ai_engine.models import RiskScore
from apps.interventions.models import Intervention
import datetime

def generate_student_report(student_id):
    """
    Template-based Natural Language Generation engine.
    Constructs a textual report summarizing the student's current status.
    """
    try:
        student = Student.objects.get(_id=student_id)
    except Student.DoesNotExist:
        return "Student not found.", "unknown"

    # 1. Basic Intro
    intro = f"{student.full_name} ({student.registration_no}) is currently enrolled in {student.class_id}."
    
    # 2. Risk Metrics
    risk_qs = RiskScore.objects.filter(student=student).order_by('-scored_at').first()
    if risk_qs:
        risk_level = risk_qs.risk_level
        score = risk_qs.score
        att_pct = risk_qs.attendance_pct
        grade_avg = risk_qs.grade_avg
        missed = risk_qs.assignments_missed
        
        # Attendance logic
        if att_pct >= 90:
            att_text = f"Attendance has been excellent at {att_pct}%."
        elif att_pct >= 75:
            att_text = f"Attendance is currently moderate at {att_pct}%."
        else:
            att_text = f"Attendance has dropped significantly to {att_pct}%, which is a primary driver of academic concern."
            
        # Grade logic
        if grade_avg >= 80:
            grade_text = f"Academically, {student.first_name} is performing well with an average score of {grade_avg}%."
        elif grade_avg >= 50:
            grade_text = f"Overall grades are average at {grade_avg}%."
        else:
            grade_text = f"Current academic performance is concerningly low at {grade_avg}%, indicating immediate need for support."
            
        # Overall Risk Summary
        if risk_level == 'red':
            risk_summary = f"Summary: EduAIMS AI flags a HIGH RISK of falling behind ({score}% severity risk score)."
        elif risk_level == 'yellow':
            risk_summary = f"Summary: EduAIMS AI indicates a MODERATE RISK of falling behind ({score}% severity risk score)."
        else:
            risk_summary = "Summary: EduAIMS AI indicates the student is currently on track and in a safe standing."
            
        metrics_paragraph = f"{att_text} {grade_text} {risk_summary}"
    else:
        risk_level = "green"
        metrics_paragraph = "Sufficient historical data is not yet available to process an AI risk score or detailed metric summary."
        
    # 3. Interventions
    interventions = Intervention.objects.filter(student=student).order_by('-created_at')[:3]
    if interventions.exists():
        int_texts = []
        for inv in interventions:
            date_str = inv.created_at.strftime('%b %d, %Y')
            status = inv.status
            itype = inv.get_intervention_type_display()
            int_texts.append(f"{itype} logged on {date_str} (Status: {status})")
            
        int_intro = f"Teacher administration has logged the following recent interventions for {student.first_name}: "
        int_paragraph = int_intro + "; ".join(int_texts) + "."
    else:
        int_paragraph = f"No corrective interventions have been issued for {student.first_name} thus far."
        
    # Assemble Report
    final_report = f"{intro}\n\n{metrics_paragraph}\n\n{int_paragraph}"
    
    return final_report, risk_level
