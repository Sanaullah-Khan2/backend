from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from eduaims.supabase_client import supabase

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_all_fees(request):
    try:
        # Get all fees
        res = supabase.table('fees').select('*').execute()
        fees = res.data or []

        # Calculate KPIs
        total_collected = sum(f['amount_paid'] or 0 for f in fees if f['status'] == 'paid')
        total_pending = sum((f['amount_due'] or 0) - (f['amount_paid'] or 0) for f in fees if f['status'] != 'paid')
        
        today = timezone.now().date().isoformat()
        defaulters = len([f for f in fees if f['status'] != 'paid' and f['due_date'] and f['due_date'] < today])
        
        total_expected = sum(f['amount_due'] or 0 for f in fees)
        collection_rate = (total_collected / total_expected * 100) if total_expected > 0 else 0

        kpis = {
            'total_collected': total_collected,
            'total_pending': total_pending,
            'defaulters': defaulters,
            'collection_rate': round(collection_rate, 2)
        }

        return Response({"success": True, "data": fees, "kpis": kpis})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_fee(request):
    try:
        data = request.data
        # Expecting: student_id, amount_due, due_date, month
        # We need to fetch student_name and class_name from students table
        student_id = data.get('student_id')
        
        student_res = supabase.table('students').select('full_name, class_name').eq('id', student_id).execute()
        if not student_res.data:
            return Response({"error": "Student not found"}, status=404)
            
        student = student_res.data[0]
        
        new_fee = {
            'student_id': student_id,
            'student_name': student['full_name'],
            'class_name': student['class_name'],
            'amount_due': data.get('amount_due', 0),
            'amount_paid': 0,
            'due_date': data.get('due_date'),
            'status': 'unpaid',
            'month': data.get('month')
        }
        
        res = supabase.table('fees').insert(new_fee).execute()
        return Response({"success": True, "data": res.data[0] if res.data else None})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_fee_paid(request, fee_id):
    try:
        fee_res = supabase.table('fees').select('*').eq('id', fee_id).execute()
        if not fee_res.data:
            return Response({"error": "Fee not found"}, status=404)
            
        fee = fee_res.data[0]
        if fee['status'] == 'paid':
            return Response({"error": "Already paid"}, status=400)
            
        amount_due = fee['amount_due']
        
        update_res = supabase.table('fees').update({
            'status': 'paid',
            'amount_paid': amount_due
        }).eq('id', fee_id).execute()
        
        # Log to audit_log
        user_id = str(request.user.id) if hasattr(request.user, 'id') else None
        supabase.table('audit_log').insert({
            'action': 'fee_marked_paid',
            'user_id': user_id,
            'details': f"Fee {fee_id} marked as paid"
        }).execute()
        
        return Response({"success": True, "data": update_res.data[0] if update_res.data else None})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_defaulters(request):
    try:
        today = timezone.now().date().isoformat()
        res = supabase.table('fees').select('*').neq('status', 'paid').lt('due_date', today).execute()
        return Response({"success": True, "data": res.data or []})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_all_salaries(request):
    try:
        res = supabase.table('salaries').select('*').execute()
        salaries = res.data or []
        
        this_month = timezone.now().strftime('%B') # e.g. 'May'
        this_year = timezone.now().year
        
        current_month_salaries = [s for s in salaries if s.get('month') == this_month and str(s.get('year')) == str(this_year)]
        
        disbursed = sum(s['net_salary'] or 0 for s in current_month_salaries if s['status'] == 'paid')
        pending = sum(s['net_salary'] or 0 for s in current_month_salaries if s['status'] != 'paid')
        staff_paid = len([s for s in current_month_salaries if s['status'] == 'paid'])
        staff_unpaid = len([s for s in current_month_salaries if s['status'] != 'paid'])
        
        kpis = {
            'disbursed': disbursed,
            'pending': pending,
            'staff_paid': staff_paid,
            'staff_unpaid': staff_unpaid
        }
        
        return Response({"success": True, "data": salaries, "kpis": kpis})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_salary(request):
    try:
        data = request.data
        # Expecting: faculty_id, basic_salary, allowances, deductions, month, year
        faculty_id = data.get('faculty_id')
        
        fac_res = supabase.table('faculty').select('name, designation').eq('id', faculty_id).execute()
        if not fac_res.data:
            return Response({"error": "Faculty not found"}, status=404)
            
        faculty = fac_res.data[0]
        
        basic = float(data.get('basic_salary', 0))
        allowances = float(data.get('allowances', 0))
        deductions = float(data.get('deductions', 0))
        net = basic + allowances - deductions
        
        new_salary = {
            'faculty_id': faculty_id,
            'faculty_name': faculty['name'],
            'designation': faculty['designation'],
            'basic_salary': basic,
            'allowances': allowances,
            'deductions': deductions,
            'net_salary': net,
            'month': data.get('month'),
            'year': data.get('year'),
            'status': 'unpaid'
        }
        
        res = supabase.table('salaries').insert(new_salary).execute()
        return Response({"success": True, "data": res.data[0] if res.data else None})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def update_salary(request, salary_id):
    try:
        data = request.data
        basic = float(data.get('basic_salary', 0))
        allowances = float(data.get('allowances', 0))
        deductions = float(data.get('deductions', 0))
        net = basic + allowances - deductions
        
        update_data = {
            'basic_salary': basic,
            'allowances': allowances,
            'deductions': deductions,
            'net_salary': net
        }
        
        res = supabase.table('salaries').update(update_data).eq('id', salary_id).execute()
        return Response({"success": True, "data": res.data[0] if res.data else None})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def pay_salary(request, salary_id):
    try:
        sal_res = supabase.table('salaries').select('*').eq('id', salary_id).execute()
        if not sal_res.data:
            return Response({"error": "Salary not found"}, status=404)
            
        if sal_res.data[0]['status'] == 'paid':
            return Response({"error": "Already paid"}, status=400)
            
        res = supabase.table('salaries').update({
            'status': 'paid',
            'paid_date': timezone.now().date().isoformat()
        }).eq('id', salary_id).execute()
        
        return Response({"success": True, "data": res.data[0] if res.data else None})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
