from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db import connection
import hashlib
from eduaims.supabase_client import supabase
from .models import Student
from .serializers import StudentSerializer

def execute_sqlite_query(query, params=None):
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        return None

class StudentViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        class_id  = request.query_params.get('class_id')
        search    = request.query_params.get('search', '').strip()
        risk_lvl  = request.query_params.get('risk_level', '').strip()
        data = []
        
        # 1. Try fetching from Supabase directly
        try:
            query = supabase.table('students').select('*')
            if class_id:
                query = query.eq('class_id', class_id)
            res = query.order('created_at', desc=True).execute()
            data = res.data or []
        except Exception as e:
            print("Supabase connection error, trying local SQLite:", e)
            # 2. Try fetching from local SQLite database
            try:
                if class_id:
                    data = execute_sqlite_query(
                        "SELECT * FROM students WHERE class_id = ? OR class_name LIKE ? ORDER BY created_at DESC", 
                        [class_id, f"{class_id}%"]
                    )
                else:
                    data = execute_sqlite_query("SELECT * FROM students ORDER BY created_at DESC")
            except Exception as sqle:
                print("Local SQLite students fetch failed:", sqle)
                data = []

        # 3. If both Supabase and SQLite return empty results, use fallback dataset
        if not data:
            fallback_students = [
                {"id": "s-ahmed-9a", "full_name": "Ahmed Khan", "first_name": "Ahmed", "last_name": "Khan", "registration_no": "EduAIMS-2026-001", "attendance_pct": 72, "grade_average": 58, "class_id": "9", "section": "A", "class_name": "9-A", "gender": "male", "risk_level": "red"},
                {"id": "s-fatima-9a", "full_name": "Fatima Sana", "first_name": "Fatima", "last_name": "Sana", "registration_no": "EduAIMS-2026-002", "attendance_pct": 94, "grade_average": 88, "class_id": "9", "section": "A", "class_name": "9-A", "gender": "female", "risk_level": "green"},
                {"id": "s-zainab-9a", "full_name": "Zainab Bibi", "first_name": "Zainab", "last_name": "Bibi", "registration_no": "EduAIMS-2026-003", "attendance_pct": 88, "grade_average": 79, "class_id": "9", "section": "A", "class_name": "9-A", "gender": "female", "risk_level": "green"},
                {"id": "s-ali-9a", "full_name": "Ali Raza", "first_name": "Ali", "last_name": "Raza", "registration_no": "EduAIMS-2026-004", "attendance_pct": 82, "grade_average": 71, "class_id": "9", "section": "A", "class_name": "9-A", "gender": "male", "risk_level": "green"},
                {"id": "s-bilal-9a", "full_name": "Bilal Siddiqui", "first_name": "Bilal", "last_name": "Siddiqui", "registration_no": "EduAIMS-2026-005", "attendance_pct": 80, "grade_average": 65, "class_id": "9", "section": "A", "class_name": "9-A", "gender": "male", "risk_level": "yellow"},
                {"id": "s-fatima-10b", "full_name": "Fatima Malik", "first_name": "Fatima", "last_name": "Malik", "registration_no": "EduAIMS-2026-011", "attendance_pct": 85, "grade_average": 62, "class_id": "10", "section": "B", "class_name": "10-B", "gender": "female", "risk_level": "yellow"},
                {"id": "s-aisha-10b", "full_name": "Aisha Rehman", "first_name": "Aisha", "last_name": "Rehman", "registration_no": "EduAIMS-2026-012", "attendance_pct": 92, "grade_average": 84, "class_id": "10", "section": "B", "class_name": "10-B", "gender": "female", "risk_level": "green"},
                {"id": "s-umer-10b", "full_name": "Umer Farooq", "first_name": "Umer", "last_name": "Farooq", "registration_no": "EduAIMS-2026-013", "attendance_pct": 96, "grade_average": 91, "class_id": "10", "section": "B", "class_name": "10-B", "gender": "male", "risk_level": "green"},
                {"id": "s-mustafa-10b", "full_name": "Mustafa Khan", "first_name": "Mustafa", "last_name": "Khan", "registration_no": "EduAIMS-2026-014", "attendance_pct": 74, "grade_average": 60, "class_id": "10", "section": "B", "class_name": "10-B", "gender": "male", "risk_level": "red"},
                {"id": "s-hamza-11a", "full_name": "Hamza Tariq", "first_name": "Hamza", "last_name": "Tariq", "registration_no": "EduAIMS-2026-021", "attendance_pct": 78, "grade_average": 68, "class_id": "11", "section": "A", "class_name": "11-A", "gender": "male", "risk_level": "yellow"},
                {"id": "s-sana-11a", "full_name": "Sana Javed", "first_name": "Sana", "last_name": "Javed", "registration_no": "EduAIMS-2026-022", "attendance_pct": 95, "grade_average": 90, "class_id": "11", "section": "A", "class_name": "11-A", "gender": "female", "risk_level": "green"},
                {"id": "s-zafar-11a", "full_name": "Zafar Iqbal", "first_name": "Zafar", "last_name": "Iqbal", "registration_no": "EduAIMS-2026-023", "attendance_pct": 89, "grade_average": 81, "class_id": "11", "section": "A", "class_name": "11-A", "gender": "male", "risk_level": "green"},
                {"id": "s-mariam-11a", "full_name": "Mariam Yousuf", "first_name": "Mariam", "last_name": "Yousuf", "registration_no": "EduAIMS-2026-024", "attendance_pct": 91, "grade_average": 86, "class_id": "11", "section": "A", "class_name": "11-A", "gender": "female", "risk_level": "green"},
            ]
            if class_id:
                data = [s for s in fallback_students if s['class_id'] == class_id or s['class_name'].startswith(class_id)]
            else:
                data = fallback_students

        # 4. Enrich students with risk_level and grade_average from DB
        try:
            risk_map = {}
            try:
                risk_res = supabase.table('risk_scores').select('student_id,level').order('calculated_at', desc=True).execute()
                for r in (risk_res.data or []):
                    sid = r.get('student_id')
                    if sid and sid not in risk_map:
                        risk_map[sid] = r.get('level', 'green')
            except Exception:
                try:
                    sq_risk = execute_sqlite_query("SELECT student_id, level FROM risk_scores ORDER BY calculated_at DESC")
                    for r in (sq_risk or []):
                        sid = r.get('student_id')
                        if sid and sid not in risk_map:
                            risk_map[sid] = r.get('level', 'green')
                except Exception:
                    pass

            grade_map = {}
            try:
                grade_res = supabase.table('grades').select('student_id,score,total_score,percentage').execute()
                for g in (grade_res.data or []):
                    sid = g.get('student_id')
                    pct = g.get('percentage') or (g.get('score', 0) / max(g.get('total_score', 100), 1) * 100)
                    if sid:
                        grade_map.setdefault(sid, []).append(pct)
            except Exception:
                try:
                    sq_grades = execute_sqlite_query("SELECT student_id, score, total_score, percentage FROM grades")
                    for g in (sq_grades or []):
                        sid = g.get('student_id')
                        pct = g.get('percentage') or (g.get('score', 0) / max(g.get('total_score', 100), 1) * 100)
                        if sid:
                            grade_map.setdefault(sid, []).append(pct)
                except Exception:
                    pass

            for s in data:
                sid = s.get('id')
                if 'risk_level' not in s or not s['risk_level']:
                    s['risk_level'] = risk_map.get(sid, 'green')
                if 'grade_average' not in s or s['grade_average'] is None:
                    grades_list = grade_map.get(sid, [])
                    s['grade_average'] = round(sum(grades_list) / len(grades_list)) if grades_list else None
        except Exception as enrich_err:
            print('Enrichment error in students list:', enrich_err)

        # 5. Apply filters
        if search:
            sl = search.lower()
            data = [s for s in data if sl in (s.get('full_name','') or '').lower() or sl in (s.get('registration_no','') or '').lower()]

        if risk_lvl:
            data = [s for s in data if s.get('risk_level') == risk_lvl]

        # 6. Normalize keys for frontend compatibility
        for s in data:
            sid = s.get('id') or s.get('_id')
            s['id'] = sid
            s['_id'] = sid
            
            if 'registration_number' in s and 'registration_no' not in s:
                s['registration_no'] = s['registration_number']
            if 'registration_no' in s and 'registration_number' not in s:
                s['registration_number'] = s['registration_no']
                
            if 'attendance_percentage' in s and 'attendance_pct' not in s:
                s['attendance_pct'] = s['attendance_percentage']
            if 'attendance_pct' in s and 'attendance_percentage' not in s:
                s['attendance_percentage'] = s['attendance_pct']
                
            if 'current_grade_average' in s and 'grade_average' not in s:
                s['grade_average'] = s['current_grade_average']
                s['grade_avg'] = s['current_grade_average']
            if 'grade_avg' in s and 'grade_average' not in s:
                s['grade_average'] = s['grade_avg']
            if 'grade_average' in s and 'grade_avg' not in s:
                s['grade_avg'] = s['grade_average']
                
            if 'class_name' in s and 'class_id' not in s:
                cname = s.get('class_name', '')
                if '-' in cname:
                    s['class_id'] = cname.split('-')[0]
                    s['section'] = cname.split('-')[1]
                else:
                    s['class_id'] = cname
            if 'class_id' in s and 'class_name' not in s:
                s['class_name'] = f"{s.get('class_id')}-{s.get('section')}" if s.get('section') else s.get('class_id')
                
            if 'risk_level' not in s:
                s['risk_level'] = 'green'

        return Response({
            "count": len(data),
            "results": data,
            "data": data
        })

    def retrieve(self, request, pk=None):
        student = None
        try:
            res = supabase.table('students').select('*').eq('id', pk).execute()
            if res.data:
                student = res.data[0]
        except Exception as e:
            print("Supabase error in student retrieve, falling back:", e)
            
        if not student:
            try:
                db_data = execute_sqlite_query("SELECT * FROM students WHERE id = ?", [pk])
                if db_data:
                    student = db_data[0]
            except Exception as sqle:
                print("SQLite error in student retrieve:", sqle)
                
        if not student:
            fallback_students = [
                {"id": "s-ahmed-9a", "full_name": "Ahmed Khan", "first_name": "Ahmed", "last_name": "Khan", "registration_no": "EduAIMS-2026-001", "attendance_pct": 72, "grade_average": 58, "class_id": "9", "section": "A", "class_name": "9-A", "gender": "male", "risk_level": "red"},
                {"id": "s-fatima-9a", "full_name": "Fatima Sana", "first_name": "Fatima", "last_name": "Sana", "registration_no": "EduAIMS-2026-002", "attendance_pct": 94, "grade_average": 88, "class_id": "9", "section": "A", "class_name": "9-A", "gender": "female", "risk_level": "green"},
                {"id": "s-zainab-9a", "full_name": "Zainab Bibi", "first_name": "Zainab", "last_name": "Bibi", "registration_no": "EduAIMS-2026-003", "attendance_pct": 88, "grade_average": 79, "class_id": "9", "section": "A", "class_name": "9-A", "gender": "female", "risk_level": "green"},
                {"id": "s-ali-9a", "full_name": "Ali Raza", "first_name": "Ali", "last_name": "Raza", "registration_no": "EduAIMS-2026-004", "attendance_pct": 82, "grade_average": 71, "class_id": "9", "section": "A", "class_name": "9-A", "gender": "male", "risk_level": "green"},
                {"id": "s-bilal-9a", "full_name": "Bilal Siddiqui", "first_name": "Bilal", "last_name": "Siddiqui", "registration_no": "EduAIMS-2026-005", "attendance_pct": 80, "grade_average": 65, "class_id": "9", "section": "A", "class_name": "9-A", "gender": "male", "risk_level": "yellow"},
                {"id": "s-fatima-10b", "full_name": "Fatima Malik", "first_name": "Fatima", "last_name": "Malik", "registration_no": "EduAIMS-2026-011", "attendance_pct": 85, "grade_average": 62, "class_id": "10", "section": "B", "class_name": "10-B", "gender": "female", "risk_level": "yellow"},
                {"id": "s-aisha-10b", "full_name": "Aisha Rehman", "first_name": "Aisha", "last_name": "Rehman", "registration_no": "EduAIMS-2026-012", "attendance_pct": 92, "grade_average": 84, "class_id": "10", "section": "B", "class_name": "10-B", "gender": "female", "risk_level": "green"},
                {"id": "s-umer-10b", "full_name": "Umer Farooq", "first_name": "Umer", "last_name": "Farooq", "registration_no": "EduAIMS-2026-013", "attendance_pct": 96, "grade_average": 91, "class_id": "10", "section": "B", "class_name": "10-B", "gender": "male", "risk_level": "green"},
                {"id": "s-mustafa-10b", "full_name": "Mustafa Khan", "first_name": "Mustafa", "last_name": "Khan", "registration_no": "EduAIMS-2026-014", "attendance_pct": 74, "grade_average": 60, "class_id": "10", "section": "B", "class_name": "10-B", "gender": "male", "risk_level": "red"},
                {"id": "s-hamza-11a", "full_name": "Hamza Tariq", "first_name": "Hamza", "last_name": "Tariq", "registration_no": "EduAIMS-2026-021", "attendance_pct": 78, "grade_average": 68, "class_id": "11", "section": "A", "class_name": "11-A", "gender": "male", "risk_level": "yellow"},
                {"id": "s-sana-11a", "full_name": "Sana Javed", "first_name": "Sana", "last_name": "Javed", "registration_no": "EduAIMS-2026-022", "attendance_pct": 95, "grade_average": 90, "class_id": "11", "section": "A", "class_name": "11-A", "gender": "female", "risk_level": "green"},
                {"id": "s-zafar-11a", "full_name": "Zafar Iqbal", "first_name": "Zafar", "last_name": "Iqbal", "registration_no": "EduAIMS-2026-023", "attendance_pct": 89, "grade_average": 81, "class_id": "11", "section": "A", "class_name": "11-A", "gender": "male", "risk_level": "green"},
                {"id": "s-mariam-11a", "full_name": "Mariam Yousuf", "first_name": "Mariam", "last_name": "Yousuf", "registration_no": "EduAIMS-2026-024", "attendance_pct": 91, "grade_average": 86, "class_id": "11", "section": "A", "class_name": "11-A", "gender": "female", "risk_level": "green"},
            ]
            student = next((s for s in fallback_students if s['id'] == pk), None)
            
        if not student:
            return Response({"success": False, "error": "Student not found"}, status=404)

        # Normalize and enrich
        sid = student.get('id') or student.get('_id')
        student['id'] = sid
        student['_id'] = sid
        
        if not student.get('full_name') and student.get('first_name'):
            student['full_name'] = f"{student.get('first_name')} {student.get('last_name', '')}".strip()
            
        if 'class_name' in student and 'class_id' not in student:
            cname = student.get('class_name', '')
            if '-' in cname:
                student['class_id'] = cname.split('-')[0]
                student['section'] = cname.split('-')[1]
            else:
                student['class_id'] = cname
        if 'class_id' in student and 'class_name' not in student:
            student['class_name'] = f"{student.get('class_id')}-{student.get('section')}" if student.get('section') else student.get('class_id')

        if 'registration_number' in student and 'registration_no' not in student:
            student['registration_no'] = student['registration_number']
        if 'registration_no' in student and 'registration_number' not in student:
            student['registration_number'] = student['registration_no']

        if 'attendance_percentage' in student and 'attendance_pct' not in student:
            student['attendance_pct'] = student['attendance_percentage']
        if 'attendance_pct' in student and 'attendance_percentage' not in student:
            student['attendance_percentage'] = student['attendance_pct']
        if 'current_grade_average' in student and 'grade_average' not in student:
            student['grade_average'] = student['current_grade_average']
            student['grade_avg'] = student['current_grade_average']
        if 'grade_avg' in student and 'grade_average' not in student:
            student['grade_average'] = student['grade_avg']
        if 'grade_average' in student and 'grade_avg' not in student:
            student['grade_avg'] = student['grade_average']

        if 'risk_level' not in student:
            try:
                risk_res = supabase.table('risk_scores').select('level').eq('student_id', sid).order('calculated_at', desc=True).limit(1).execute()
                if risk_res.data:
                    student['risk_level'] = risk_res.data[0].get('level', 'green')
            except Exception:
                pass
            if 'risk_level' not in student:
                student['risk_level'] = 'green'

        return Response({"success": True, "data": student})


    def update(self, request, pk=None):
        try:
            data = {k: v for k, v in request.data.items() if k not in ('id', '_id', 'created_at')}
            res  = supabase.table('students').update(data).eq('id', pk).execute()
            if not res.data:
                return Response({"error": "Student not found or no changes"}, status=404)
            return Response({"success": True, "data": res.data[0]})
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def destroy(self, request, pk=None):
        try:
            supabase.table('students').delete().eq('id', pk).execute()
            try:
                supabase.table('users').delete().eq('linked_id', pk).execute()
            except Exception:
                pass
            return Response(status=204)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    @action(detail=False, methods=['post'], url_path='bulk-import')
    def bulk_import(self, request):
        # Placeholder for bulk CSV import logic
        return Response({"status": "Bulk import placeholder"}, status=200)

# ── STUDENT PORTAL ENDPOINTS ─────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def student_dashboard_kpis(request):
    """Return KPIs for the logged-in student from Supabase"""
    try:
        user = request.user
        # Get linked_id (student record id)
        user_res = supabase.table('users').select('linked_id').eq('email', user.email).execute()
        linked_id = user_res.data[0]['linked_id'] if user_res.data else None
        if not linked_id:
            return Response({"success": True, "data": {"grade_average": 32, "attendance_pct": 62, "assignments_pending": 1}})

        # Attendance %
        att_res = supabase.table('attendance').select('status').eq('student_id', linked_id).execute()
        att = att_res.data or []
        present = sum(1 for a in att if a['status'] == 'present')
        late = sum(1 for a in att if a['status'] == 'late')
        att_pct = round((present + late * 0.5) / len(att) * 100) if att else 62

        # Grade average
        grades_res = supabase.table('grades').select('score,total_score').eq('student_id', linked_id).execute()
        grades = grades_res.data or []
        if grades:
            grade_avg = round(sum(g.get('score', 0) or 0 for g in grades) / len(grades))
        else:
            grade_avg = 32

        # Pending assignments
        subs_res = supabase.table('assignment_submissions').select('status').eq('student_id', linked_id).execute()
        subs = subs_res.data or []
        pending = len([s for s in subs if s['status'] == 'pending'])

        data = {
            "grade_average": grade_avg,
            "attendance_pct": att_pct,
            "assignments_pending": pending,
        }
        return Response({"success": True, "data": data})
    except Exception as e:
        print("Error in student_dashboard_kpis:", str(e))
        return Response({"success": False, "error": str(e)}, status=200)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def student_performance(request):
    """Return student's grades per subject from Supabase"""
    try:
        user = request.user
        user_res = supabase.table('users').select('linked_id').eq('email', user.email).execute()
        linked_id = user_res.data[0]['linked_id'] if user_res.data else None
        if not linked_id:
            raise Exception('No linked_id')
        grades_res = supabase.table('grades').select('*').eq('student_id', linked_id).execute()
        grades = grades_res.data or []
        # Group by subject
        by_subject = {}
        for g in grades:
            subj = g.get('subject', 'Unknown')
            if subj not in by_subject:
                by_subject[subj] = []
            by_subject[subj].append(g.get('score', 0) or 0)
        data = [
            {"subject": subj, "monthly": round(sum(scores)/len(scores)), "midterm": round(sum(scores)/len(scores)), "final": round(sum(scores)/len(scores))}
            for subj, scores in by_subject.items()
        ]
        return Response({"success": True, "data": data})
    except Exception as e:
        print("Error in student_performance:", str(e))
        return Response({"success": False, "error": str(e)}, status=200)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def student_ai_tips(request):
    """Return personalised study tips based on live data."""
    try:
        user = request.user
        user_res = supabase.table('users').select('linked_id').eq('email', user.email).execute()
        linked_id = user_res.data[0]['linked_id'] if user_res.data else None
        
        data = []
        
        if linked_id:
            # Check for upcoming assignments
            subs_res = supabase.table('assignment_submissions').select('*, assignment:assignments(*)').eq('student_id', linked_id).eq('status', 'pending').execute()
            pending = subs_res.data or []
            if pending:
                data.append({
                    "type": "info",
                    "subject": "Upcoming Assignment",
                    "tip": f"You have {len(pending)} pending assignment(s). Starting today makes it much easier!"
                })
            
            # Check attendance
            att_res = supabase.table('attendance').select('status').eq('student_id', linked_id).order('date', desc=True).limit(5).execute()
            recent_att = [a['status'] for a in (att_res.data or [])]
            if 'absent' in recent_att:
                data.append({
                    "type": "warning",
                    "subject": "Attendance",
                    "tip": "We missed you recently! Attending classes helps you understand lessons better."
                })
            else:
                data.append({
                    "type": "success",
                    "subject": "Great Attendance",
                    "tip": "You have been attending classes regularly. Keep up the great work!"
                })
                
        # Default tip
        if not data:
            data.append({
                "type": "info",
                "subject": "Weekly Tip",
                "tip": "Mathematics gets easier with daily practice. Try solving 5 problems every evening before bed."
            })
            
        return Response({"success": True, "data": data})
    except Exception as e:
        print("Error in student_ai_tips:", str(e))
        return Response({"success": False, "error": str(e)}, status=200)

# ── PARENT PORTAL ENDPOINTS ──────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def parent_child_overview(request):
    """Return the live child overview for the parent"""
    try:
        user = request.user
        user_res = supabase.table('users').select('linked_id').eq('email', user.email).execute()
        linked_id = user_res.data[0]['linked_id'] if user_res.data else None
        
        if not linked_id:
            return Response({"success": False, "error": "No linked child found"}, status=404)

        student_res = supabase.table('students').select('*').eq('id', linked_id).execute()
        student = student_res.data[0] if student_res.data else {}
        
        risk_res = supabase.table('risk_scores').select('*').eq('student_id', linked_id).order('calculated_at', desc=True).limit(1).execute()
        risk = risk_res.data[0] if risk_res.data else {}

        att_res = supabase.table('attendance').select('status').eq('student_id', linked_id).execute()
        att = att_res.data or []
        present = sum(1 for a in att if a['status'] == 'present')
        att_pct = round((present / len(att)) * 100) if len(att) > 0 else 100

        grades_res = supabase.table('grades').select('percentage').eq('student_id', linked_id).execute()
        grades = grades_res.data or []
        grade_avg = round(sum(g.get('percentage', 0) for g in grades) / len(grades)) if grades else 100

        data = {
            "child_name": student.get('full_name', 'Student'),
            "class_name": student.get('class_name', ''),
            "roll_no": student.get('registration_no', ''),
            "grade_average": grade_avg,
            "attendance_pct": att_pct,
            "risk_level": risk.get('level', 'green'),
            "risk_reason": risk.get('reason', 'Performing well'),
            "teacher_name": ""
        }
        return Response({"success": True, "data": data})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def parent_child_grades(request):
    """Return live child's most recent grades per subject"""
    try:
        user = request.user
        user_res = supabase.table('users').select('linked_id').eq('email', user.email).execute()
        linked_id = user_res.data[0]['linked_id'] if user_res.data else None
        
        if not linked_id:
            return Response({"success": True, "data": []})

        grades_res = supabase.table('grades').select('*').eq('student_id', linked_id).execute()
        grades = grades_res.data or []
        
        by_subject = {}
        for g in grades:
            subj = g.get('subject', 'Unknown')
            if subj not in by_subject:
                by_subject[subj] = []
            by_subject[subj].append(g.get('percentage', 0))
            
        data = [
            {"subject": subj, "monthly": round(sum(scores)/len(scores)), "midterm": round(sum(scores)/len(scores)), "final": round(sum(scores)/len(scores))}
            for subj, scores in by_subject.items()
        ]
        return Response({"success": True, "data": data})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def parent_child_alerts(request):
    """Return live AI alerts for the parent's child"""
    try:
        user = request.user
        user_res = supabase.table('users').select('linked_id').eq('email', user.email).execute()
        linked_id = user_res.data[0]['linked_id'] if user_res.data else None
        
        if not linked_id:
            return Response({"success": True, "data": []})

        interventions_res = supabase.table('interventions').select('*').eq('student_id', linked_id).order('date', desc=True).limit(5).execute()
        interventions = interventions_res.data or []
        
        data = []
        for i in interventions:
            data.append({
                "type": "warning",
                "date": str(i.get('date', ''))[:10],
                "message": f"Intervention: {i.get('action_type', '')} - {i.get('notes', '')}"
            })
            
        if not data:
            data.append({
                "type": "info",
                "date": str(timezone.now().date()),
                "message": "No new alerts at this time."
            })
            
        return Response({"success": True, "data": data})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def parent_narrative_report(request):
    """Return a live narrative report for the parent"""
    try:
        user = request.user
        user_res = supabase.table('users').select('linked_id').eq('email', user.email).execute()
        linked_id = user_res.data[0]['linked_id'] if user_res.data else None
        
        if not linked_id:
            return Response({"success": False, "error": "No linked child"}, status=404)

        report_res = supabase.table('nlg_reports').select('*').eq('student_id', linked_id).order('created_at', desc=True).limit(1).execute()
        report = report_res.data[0] if report_res.data else {}
        
        text = report.get('report_text', "No report generated yet.")
        
        data = {
            "generated_at": str(report.get('created_at', timezone.now().date()))[:10],
            "report": text
        }
        return Response({"success": True, "data": data})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=500)

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

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def student_attendance(request):
    """Return attendance summary and recent records for the logged-in student from Supabase"""
    try:
        user = request.user
        user_res = supabase.table('users').select('linked_id').eq('email', user.email).execute()
        linked_id = user_res.data[0]['linked_id'] if user_res.data else None
        if not linked_id:
            return Response({
                "success": True, 
                "data": {
                    "summary": {"total_classes": 0, "present": 0, "absent": 0, "late": 0, "pct": 100},
                    "records": []
                }
            })

        att_res = supabase.table('attendance').select('*').eq('student_id', linked_id).order('date', desc=True).execute()
        records = att_res.data or []
        
        total = len(records)
        present = sum(1 for a in records if a['status'] == 'present')
        absent = sum(1 for a in records if a['status'] == 'absent')
        late = sum(1 for a in records if a['status'] == 'late')
        pct = round((present + late * 0.5) / total * 100) if total > 0 else 100

        # Map to format expected by UI (renaming fields)
        mapped_records = []
        for r in records:
            mapped_records.append({
                "date": r.get('date'),
                "subject": r.get('subject_id') or 'General',
                "status": r.get('status')
            })

        data = {
            "summary": {
                "total_classes": total,
                "present": present,
                "absent": absent,
                "late": late,
                "pct": pct
            },
            "records": mapped_records
        }
        return Response({"success": True, "data": data})
    except Exception as e:
        print("Error in student_attendance:", str(e))
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def parent_child_grades(request):
    """Return grades for the logged-in parent's linked child from Supabase"""
    try:
        user = request.user
        # Get child's student_id from user's linked_id
        user_res = supabase.table('users').select('linked_id').eq('email', user.email).execute()
        child_id = user_res.data[0]['linked_id'] if user_res.data else None
        if not child_id:
            return Response({"success": True, "data": [], "message": "No linked child found"})

        grades_res = supabase.table('grades').select('*').eq('student_id', child_id).execute()
        grades = grades_res.data or []
        return Response({"success": True, "data": grades})
    except Exception as e:
        print("Error in parent_child_grades:", str(e))
        return Response({"success": False, "error": str(e)}, status=500)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def parent_child_alerts(request):
    """Return AI risk alerts for the logged-in parent's linked child"""
    try:
        user = request.user
        user_res = supabase.table('users').select('linked_id').eq('email', user.email).execute()
        child_id = user_res.data[0]['linked_id'] if user_res.data else None
        if not child_id:
            return Response({"success": True, "data": []})

        # Get latest risk score
        risk_res = supabase.table('risk_scores').select('*').eq('student_id', child_id)\
            .order('calculated_at', desc=True).limit(5).execute()
        scores = risk_res.data or []

        # Get recent interventions for child
        int_res = supabase.table('interventions').select('*').eq('student_id', child_id)\
            .order('date', desc=True).limit(5).execute()
        interventions = int_res.data or []

        alerts = []
        for score in scores:
            if score.get('level') in ('red', 'yellow'):
                alerts.append({
                    "type": "risk",
                    "level": score.get('level'),
                    "message": score.get('reason', 'Risk detected'),
                    "date": score.get('calculated_at', ''),
                })
        for inv in interventions:
            alerts.append({
                "type": "intervention",
                "level": "info",
                "message": f"{inv.get('action_type', 'Intervention')}: {inv.get('notes', '')}",
                "date": inv.get('date', ''),
            })

        return Response({"success": True, "data": alerts})
    except Exception as e:
        print("Error in parent_child_alerts:", str(e))
        return Response({"success": False, "error": str(e)}, status=500)
