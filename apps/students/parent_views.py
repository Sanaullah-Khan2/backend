from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from eduaims.supabase_client import supabase

def get_linked_id(request):
    """Helper to verify parent role and extract linked_id"""
    user = request.user
    sb = supabase
    res = sb.table('users').select('role, linked_id').eq('email', user.email).execute()
    if not res.data or res.data[0]['role'] != 'parent':
        return None
    return res.data[0]['linked_id']

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def child_overview(request):
    try:
        linked_id = get_linked_id(request)
        if not linked_id:
            return Response({"error": "Unauthorized or not a parent"}, status=403)
            
        student_res = supabase.table('students').select('*').eq('id', linked_id).execute()
        if not student_res.data:
            return Response({"error": "Child not found"}, status=404)
        student = student_res.data[0]
        
        # Calculate Risk Friendly Label (Score 0-39: Doing Well, 40-69: Needs Some Attention, 70-100: Please Contact School)
        risk_score = student.get('risk_score', 0) # Assumes risk_score is periodically updated in student record
        if risk_score < 40:
            risk_label = "Doing Well ✓"
        elif risk_score < 70:
            risk_label = "Needs Some Attention"
        else:
            risk_label = "Please Contact School"
            
        # Attendance KPI
        attendance_pct = student.get('attendance_pct', 0)
        
        # Academic KPI
        grade_avg = student.get('grade_avg', 0)
        if grade_avg > 80:
            academic_status = "Above Average"
        elif grade_avg > 60:
            academic_status = "Average"
        else:
            academic_status = "Needs Support"
            
        # Fee Status KPI
        fees_res = supabase.table('fees').select('amount_due, amount_paid, status').eq('student_id', linked_id).neq('status', 'paid').execute()
        if fees_res.data and len(fees_res.data) > 0:
            total_due = sum((f['amount_due'] or 0) - (f['amount_paid'] or 0) for f in fees_res.data)
            fee_status = f"Due: PKR {total_due:,}"
        else:
            fee_status = "Paid"

        data = {
            "child_name": student.get('name'),
            "class_name": student.get('class_name'),
            "section": student.get('section'),
            "registration_no": student.get('registration_no'),
            "risk_label": risk_label,
            "attendance_kpi": f"{attendance_pct}% Present This Month",
            "academic_status": academic_status,
            "fee_status": fee_status
        }
        
        return Response({"success": True, "data": data})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def attendance(request):
    try:
        linked_id = get_linked_id(request)
        if not linked_id:
            return Response({"error": "Unauthorized or not a parent"}, status=403)
            
        month = request.query_params.get('month') # e.g. 2025-05
        
        query = supabase.table('attendance').select('*').eq('student_id', linked_id)
        if month:
            query = query.like('date', f"{month}-%")
            
        res = query.execute()
        return Response({"success": True, "data": res.data or []})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def monthly_report(request):
    try:
        linked_id = get_linked_id(request)
        if not linked_id:
            return Response({"error": "Unauthorized or not a parent"}, status=403)
            
        month = request.query_params.get('month') # e.g. 2025-05
        
        query = supabase.table('nlg_reports').select('*').eq('student_id', linked_id)
        if month:
            query = query.eq('month', month)
            
        res = query.order('created_at', desc=True).limit(1).execute()
        return Response({"success": True, "data": res.data[0] if res.data else None})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def fees(request):
    try:
        linked_id = get_linked_id(request)
        if not linked_id:
            return Response({"error": "Unauthorized or not a parent"}, status=403)
            
        res = supabase.table('fees').select('*').eq('student_id', linked_id).order('due_date', desc=True).execute()
        return Response({"success": True, "data": res.data or []})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)
