from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import hashlib
from eduaims.supabase_client import supabase
from .models import Student
from .serializers import StudentSerializer

class StudentViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        try:
            # Fetch from Supabase directly
            res = supabase.table('students').select('*').order('created_at', desc=True).execute()
            data = res.data or []
            return Response({
                "count": len(data),
                "results": data
            })
        except Exception as e:
            print("Supabase error in Student list:", e)
            return Response({"count": 0, "results": []})

    def retrieve(self, request, pk=None):
        try:
            res = supabase.table('students').select('*').eq('id', pk).execute()
            if not res.data:
                return Response(status=404)
            return Response(res.data[0])
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    @action(detail=False, methods=['post'], url_path='bulk-import')
    def bulk_import(self, request):
        # Placeholder for bulk CSV import logic
        return Response({"status": "Bulk import placeholder"}, status=200)

# ── STUDENT PORTAL ENDPOINTS ─────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def student_dashboard_kpis(request):
    """Return KPIs for the student dashboard (mock data)"""
    data = {
        "grade_average": 78,
        "attendance_pct": 82,
        "assignments_pending": 3,
        "rank_in_class": 12,
        "subjects_total": 7
    }
    return Response({"success": True, "data": data})

@api_view(['GET'])
@permission_classes([AllowAny])
def student_performance(request):
    """Return student's recent grade history per subject"""
    data = [
        {"subject": "Mathematics",   "monthly": 72, "midterm": 68, "final": 75},
        {"subject": "Physics",        "monthly": 80, "midterm": 76, "final": 82},
        {"subject": "Chemistry",      "monthly": 65, "midterm": 70, "final": 69},
        {"subject": "English",        "monthly": 88, "midterm": 85, "final": 90},
        {"subject": "Computer Sci",   "monthly": 92, "midterm": 88, "final": 95},
        {"subject": "Urdu",           "monthly": 70, "midterm": 73, "final": 71},
        {"subject": "Islamiyat",      "monthly": 78, "midterm": 80, "final": 82},
    ]
    return Response({"success": True, "data": data})

@api_view(['GET'])
@permission_classes([AllowAny])
def student_ai_tips(request):
    """Return personalized AI study tips based on performance"""
    data = [
        {
            "type": "warning",
            "subject": "Chemistry",
            "tip": "Your Chemistry scores have been below 70. Consider reviewing Chapter 5 and 6 exercises."
        },
        {
            "type": "success",
            "subject": "Computer Science",
            "tip": "Excellent performance in Computer Science! You are ranked in the top 10% of your class."
        },
        {
            "type": "info",
            "subject": "Attendance",
            "tip": "Your attendance is 82%. Try to maintain above 85% to avoid academic penalties."
        },
        {
            "type": "info",
            "subject": "Mathematics",
            "tip": "Practice more algebra problems. Your mid-term score dropped from last month."
        }
    ]
    return Response({"success": True, "data": data})

# ── PARENT PORTAL ENDPOINTS ──────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def parent_child_overview(request):
    """Return the child overview for the parent (mock data)"""
    data = {
        "child_name": "Ali Hassan",
        "class_name": "10-A",
        "roll_no": "10A-15",
        "grade_average": 74,
        "attendance_pct": 80,
        "risk_level": "yellow",
        "risk_reason": "Attendance dropped below 82% this month",
        "teacher_name": "Mr. Asad Khan"
    }
    return Response({"success": True, "data": data})

@api_view(['GET'])
@permission_classes([AllowAny])
def parent_child_grades(request):
    """Return child's most recent grades per subject"""
    data = [
        {"subject": "Mathematics",   "monthly": 70, "midterm": 65, "final": 72},
        {"subject": "Physics",        "monthly": 78, "midterm": 74, "final": 79},
        {"subject": "Chemistry",      "monthly": 60, "midterm": 64, "final": 66},
        {"subject": "English",        "monthly": 85, "midterm": 82, "final": 88},
        {"subject": "Computer Sci",   "monthly": 90, "midterm": 87, "final": 92},
        {"subject": "Urdu",           "monthly": 68, "midterm": 72, "final": 70},
        {"subject": "Islamiyat",      "monthly": 75, "midterm": 78, "final": 80},
    ]
    return Response({"success": True, "data": data})

@api_view(['GET'])
@permission_classes([AllowAny])
def parent_child_alerts(request):
    """Return AI alerts for the parent's child"""
    data = [
        {
            "type": "warning",
            "date": "2024-03-28",
            "message": "Ali's Mathematics score dropped from 78 to 65 this month. Consider tutoring support."
        },
        {
            "type": "info",
            "date": "2024-03-25",
            "message": "Attendance this month is 80%, slightly below the 85% recommended threshold."
        },
        {
            "type": "success",
            "date": "2024-03-20",
            "message": "Ali scored 92% in Computer Science Final — top performer in class!"
        }
    ]
    return Response({"success": True, "data": data})

@api_view(['GET'])
@permission_classes([AllowAny])
def parent_narrative_report(request):
    """Return a plain-text narrative report for the parent"""
    data = {
        "generated_at": "2024-03-28",
        "report": (
            "Ali Hassan is currently performing at an average level across all subjects with an overall grade average "
            "of 74%. His strongest subject this term is Computer Science (92%) where he consistently ranks in the top "
            "10% of the class. Areas requiring attention include Mathematics and Chemistry, where scores have shown a "
            "slight downward trend this month. "
            "His attendance currently stands at 80%, which is slightly below the recommended 85% threshold. Consistent "
            "class attendance is strongly encouraged to prevent further academic risk. "
            "The AI Engine has flagged Ali as a Yellow Risk student this month, primarily due to his attendance and "
            "Math performance. We recommend reviewing study habits and attending extra help sessions if available."
        )
    }
    return Response({"success": True, "data": data})

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def enroll_student(request):
    try:
        user = request.user
        sb = supabase
        # Check if admin
        req_user_res = sb.table('users').select('role, id').eq('email', user.email).execute()
        if not req_user_res.data or req_user_res.data[0]['role'] != 'admin':
            return Response({"error": "Admin access required"}, status=403)
            
        data = request.data
        admin_id = req_user_res.data[0]['id']
        student_email = data.get('email', '').strip().lower()
        
        # Check if email already exists in users table
        existing_user = sb.table('users').select('id').eq('email', student_email).execute()
        if existing_user.data:
            return Response({"error": f"A user with email '{student_email}' already exists. Please use a different email."}, status=409)
        
        # Check if email already exists in students table
        existing_student = sb.table('students').select('id').eq('email', student_email).execute()
        if existing_student.data:
            return Response({"error": f"A student with email '{student_email}' is already enrolled."}, status=409)
        
        # Generate reg no
        year = timezone.now().year
        count_res = sb.table('students').select('id', count='exact').execute()
        count = count_res.count or 0
        reg_no = f"EduAIMS-{year}-{str(count + 1).zfill(3)}"
        
        new_student = {
            'full_name': data.get('name'),
            'email': student_email,
            'class_name': data.get('class_name'),
            'parent_email': student_email, # using student email as fallback
            'registration_no': reg_no,
            'is_active': True
        }
        
        stu_res = sb.table('students').insert(new_student).execute()
        if not stu_res.data:
            return Response({"error": "Failed to create student"}, status=500)
            
        # Create user account
        salt = 'eduaims_fixed_salt_2024'
        password = 'Student@123'
        password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        
        new_user = {
            'email': student_email,
            'password_hash': password_hash,
            'role': 'student',
            'name': data.get('name'),
            'is_active': True,
            'linked_id': stu_res.data[0]['id']
        }
        sb.table('users').insert(new_user).execute()
        
        # Send email
        send_mail(
            'Welcome to EduAIMS',
            f'Your account is created. Email: {student_email}, Password: {password}',
            settings.DEFAULT_FROM_EMAIL or 'noreply@eduaims.com',
            [student_email],
            fail_silently=True,
        )
        
        sb.table('audit_log').insert({
            'action': 'student_enrolled',
            'user_id': admin_id,
            'details': f"Manually enrolled student {student_email}"
        }).execute()
        
        return Response({"success": True, "message": "Student enrolled successfully"})
    except Exception as e:
        error_msg = str(e)
        if '23505' in error_msg or 'already exists' in error_msg:
            return Response({"error": f"A user with this email already exists. Please use a different email."}, status=409)
        return Response({"success": False, "error": error_msg}, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def request_enrollment(request):
    try:
        data = request.data
        new_request = {
            'student_name': data.get('name'),
            'father_name': data.get('father_name'),
            'email': data.get('email'),
            'phone': data.get('phone'),
            'class_name': data.get('class_name'),
            'status': 'pending',
            'requested_at': timezone.now().isoformat()
        }
        supabase.table('enrollment_requests').insert(new_request).execute()
        return Response({"success": True, "message": "Your request has been submitted. Wait for admin approval."})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_enrollment_requests(request):
    try:
        res = supabase.table('enrollment_requests').select('*').order('requested_at', desc=True).execute()
        return Response({"success": True, "data": res.data})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def approve_enrollment(request, request_id):
    try:
        user = request.user
        sb = supabase
        req_user_res = sb.table('users').select('role, id').eq('email', user.email).execute()
        if not req_user_res.data or req_user_res.data[0]['role'] != 'admin':
            return Response({"error": "Admin access required"}, status=403)
        admin_id = req_user_res.data[0]['id']
        
        enr_req_res = sb.table('enrollment_requests').select('*').eq('id', request_id).execute()
        if not enr_req_res.data:
            return Response({"error": "Request not found"}, status=404)
        enr = enr_req_res.data[0]
        
        year = timezone.now().year
        count_res = sb.table('students').select('id', count='exact').execute()
        count = count_res.count or 0
        reg_no = f"EduAIMS-{year}-{str(count + 1).zfill(3)}"
        
        new_student = {
            'full_name': enr['student_name'],
            'email': enr['email'],
            'class_name': enr['class_name'],
            'parent_email': enr['email'],
            'registration_no': reg_no,
            'is_active': True
        }
        
        stu_res = sb.table('students').insert(new_student).execute()
        
        salt = 'eduaims_fixed_salt_2024'
        password = 'Student@123'
        password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        
        new_user = {
            'email': enr['email'],
            'password_hash': password_hash,
            'role': 'student',
            'name': enr['student_name'],
            'is_active': True,
            'linked_id': stu_res.data[0]['id']
        }
        sb.table('users').insert(new_user).execute()
        
        sb.table('enrollment_requests').update({
            'status': 'approved',
            'reviewed_by': admin_id,
            'reviewed_at': timezone.now().isoformat()
        }).eq('id', request_id).execute()
        
        send_mail(
            'Enrollment Approved',
            f'Your enrollment is approved. Email: {enr["email"]}, Password: {password}',
            settings.DEFAULT_FROM_EMAIL or 'noreply@eduaims.com',
            [enr['email']],
            fail_silently=True,
        )
        
        return Response({"success": True, "message": "Enrollment approved"})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reject_enrollment(request, request_id):
    try:
        user = request.user
        sb = supabase
        req_user_res = sb.table('users').select('role, id').eq('email', user.email).execute()
        if not req_user_res.data or req_user_res.data[0]['role'] != 'admin':
            return Response({"error": "Admin access required"}, status=403)
        admin_id = req_user_res.data[0]['id']
        
        reason = request.data.get('rejection_reason', 'Not specified')
        
        enr_req_res = sb.table('enrollment_requests').select('*').eq('id', request_id).execute()
        if not enr_req_res.data:
            return Response({"error": "Request not found"}, status=404)
        enr = enr_req_res.data[0]
        
        sb.table('enrollment_requests').update({
            'status': 'rejected',
            'reviewed_by': admin_id,
            'reviewed_at': timezone.now().isoformat(),
            'rejection_reason': reason
        }).eq('id', request_id).execute()
        
        send_mail(
            'Enrollment Rejected',
            f'Your enrollment request was not approved. Reason: {reason}. Please contact the school.',
            settings.DEFAULT_FROM_EMAIL or 'noreply@eduaims.com',
            [enr['email']],
            fail_silently=True,
        )
        
        return Response({"success": True, "message": "Enrollment rejected"})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)
