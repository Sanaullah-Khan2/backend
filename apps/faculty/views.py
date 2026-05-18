from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from eduaims.supabase_client import supabase
from .models import Faculty
from .serializers import FacultySerializer

class FacultyViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        try:
            res = supabase.table('faculty').select('*').order('joined_date', desc=True).execute()
            # DRF pagination isn't strictly needed if we just return the array, 
            # but to match the previous paginated response format (data.results), we wrap it:
            data = res.data or []
            return Response({
                "count": len(data),
                "results": data
            })
        except Exception as e:
            # Fallback for when the table isn't created yet or other errors
            print("Supabase error in Faculty list:", e)
            return Response({"count": 0, "results": []})

    def create(self, request):
        try:
            # The manual enrollment logic will go here.
            # In the previous step, we had FacultySerializer handling email validation and user creation.
            # We can replicate that logic here directly.
            data = request.data
            email = data.get('email', '').lower().strip()
            role = data.get('role', 'teacher')
            
            # Check for existing user
            existing = supabase.table('users').select('id').eq('email', email).execute()
            if existing.data:
                return Response({"error": "A user with this email already exists."}, status=409)
            
            # Generate random password
            import random, string, hashlib
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            salt = 'eduaims_fixed_salt_2024'
            password_hash = hashlib.sha256((salt + password).encode()).hexdigest()
            
            # Insert into users
            user_data = {
                'email': email,
                'password_hash': password_hash,
                'role': role,
                'name': data.get('full_name'),
                'is_active': True,
            }
            user_res = supabase.table('users').insert(user_data).execute()
            if not user_res.data:
                return Response({"error": "Failed to create user account."}, status=500)
            user_id = user_res.data[0]['id']
            
            # Generate employee ID
            import uuid
            emp_id = f"EMP-{str(uuid.uuid4())[:8].upper()}"
            
            # Insert into faculty
            faculty_data = {
                'user_id': user_id,
                'employee_id': emp_id,
                'full_name': data.get('full_name'),
                'subject_specialization': data.get('subject_specialization'),
                'contact_number': data.get('contact_number'),
                'classes_assigned': data.get('classes_assigned', ''),
            }
            fac_res = supabase.table('faculty').insert(faculty_data).execute()
            if not fac_res.data:
                return Response({"error": "Failed to create faculty profile."}, status=500)
            faculty_id = fac_res.data[0]['id']
            
            # Link back
            supabase.table('users').update({'linked_id': faculty_id}).eq('id', user_id).execute()
            
            return Response(fac_res.data[0], status=201)
        except Exception as e:
            print("Error creating faculty:", e)
            return Response({"error": str(e)}, status=500)

    def retrieve(self, request, pk=None):
        try:
            res = supabase.table('faculty').select('*').eq('id', pk).execute()
            if not res.data:
                return Response(status=404)
            return Response(res.data[0])
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def partial_update(self, request, pk=None):
        try:
            update_data = request.data
            res = supabase.table('faculty').update(update_data).eq('id', pk).execute()
            if not res.data:
                return Response(status=404)
            return Response(res.data[0])
        except Exception as e:
            return Response({"error": str(e)}, status=500)

# ── TEACHER PORTAL MOCK APIS ──────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def teacher_dashboard_kpis(request):
    """Return high-level KPIs for the Teacher Dashboard"""
    faculty_id = request.GET.get('faculty_id')
    try:
        classes = []
        if faculty_id:
            classes_res = supabase.table('faculty_classes').select('*').eq('faculty_id', faculty_id).execute()
            classes = classes_res.data or []
            
        total_classes = len(classes)
        total_students = sum(c.get('student_count', 0) for c in classes)
        
        risk_res = supabase.table('risk_scores').select('id', count='exact').in_('risk_level', ['red', 'yellow']).execute()
        students_at_risk = risk_res.count or 0
        
        data = {
            "total_classes": total_classes,
            "total_students": total_students,
            "assignments_pending": 0,
            "students_at_risk": students_at_risk
        }
        return Response({"success": True, "data": data})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
def teacher_classes(request):
    """Return classes assigned to the teacher, filtered by faculty_id if provided."""
    try:
        faculty_id = request.GET.get('faculty_id')
        
        query = supabase.table('faculty_classes').select('*')
        if faculty_id:
            query = query.eq('faculty_id', faculty_id)
        res = query.execute()
        
        data = res.data or []
        return Response({"success": True, "data": data})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
def teacher_alerts(request):
    """Return students at risk in the teacher's classes"""
    try:
        res = supabase.table('risk_scores').select('*, student:students(*)').in_('risk_level', ['red', 'yellow']).execute()
        data = res.data or []
        alerts = []
        for row in data:
            student = row.get('student') or {}
            alerts.append({
                "id": row.get('id'),
                "name": student.get('full_name', 'Unknown'),
                "class": student.get('class_name', 'Unknown'),
                "score": row.get('score'),
                "level": row.get('risk_level'),
                "reason": row.get('top_factors', [''])[0] if row.get('top_factors') else "Unknown reason",
            })
        return Response({"success": True, "data": alerts})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
def teacher_highlights(request):
    """Return teacher-relevant AI highlights/notices."""
    now = timezone.now().isoformat()
    try:
        # Get latest risk scores
        risk_res = supabase.table('risk_scores').select('*, student:students(*)').in_('risk_level', ['red', 'yellow']).order('created_at', desc=True).limit(5).execute()
        data = []
        for idx, row in enumerate(risk_res.data or []):
            student = row.get('student') or {}
            data.append({
                "id": idx + 1,
                "type": "at_risk" if row.get('risk_level') == 'red' else "warning",
                "severity": "high" if row.get('risk_level') == 'red' else "medium",
                "title": f"{student.get('full_name')} is at {row.get('risk_level')} risk",
                "subtitle": f"Class {student.get('class_name')} · AI Monitor",
                "link": "/teacher/ai-alerts",
                "created_at": row.get('created_at') or now
            })
        return Response({"success": True, "data": data})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)
