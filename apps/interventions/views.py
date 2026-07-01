from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import connection
from eduaims.supabase_client import supabase

def execute_sqlite_query(query, params=None):
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        if cursor.description:
            columns = [col[0] for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        return None

def execute_write_query(query, params=None):
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])

class InterventionViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        student_id = request.query_params.get('student_id')
        data = []
        try:
            query = supabase.table('interventions').select('*').order('date', desc=True)
            if student_id:
                query = query.eq('student_id', student_id)
            res = query.execute()
            data = res.data or []
        except Exception as e:
            print("Supabase error in interventions list, falling back to SQLite:", e)
            try:
                if student_id:
                    data = execute_sqlite_query(
                        "SELECT * FROM interventions WHERE student_id = ? ORDER BY date DESC",
                        [student_id]
                    )
                else:
                    data = execute_sqlite_query(
                        "SELECT * FROM interventions ORDER BY date DESC"
                    )
            except Exception as sqle:
                print("SQLite error in interventions list:", sqle)
                data = []

        # Enrich data for frontend compatibility
        for row in data:
            row['id'] = row.get('id')
            row['_id'] = row.get('id')
            row['student'] = row.get('student_id')
            row['intervention_type'] = row.get('action_type')
            row['intervention_type_display'] = row.get('action_type')
            row['status'] = row.get('outcome')
            # If student_name is missing, try to resolve it from student_id
            if not row.get('student_name') and row.get('student_id'):
                try:
                    s_res = supabase.table('students').select('full_name').eq('id', row.get('student_id')).execute()
                    if s_res.data:
                        row['student_name'] = s_res.data[0].get('full_name')
                except Exception:
                    pass
                if not row.get('student_name'):
                    try:
                        st_fallback = execute_sqlite_query("SELECT full_name FROM students WHERE id = ?", [row.get('student_id')])
                        if st_fallback:
                            row['student_name'] = st_fallback[0].get('full_name')
                    except Exception:
                        pass
            
        return Response({
            "count": len(data),
            "results": data,
            "data": data
        })

    def create(self, request):
        data = request.data
        student_id = data.get('student') or data.get('student_id')
        action_type = data.get('intervention_type') or data.get('action_type')
        outcome = data.get('status') or data.get('outcome') or 'pending'
        notes = data.get('notes', '')
        follow_up_date = data.get('follow_up_date')

        if not student_id or not action_type:
            return Response({"error": "student and intervention_type are required"}, status=400)

        # Lookup student name
        student_name = "Unknown Student"
        try:
            st_res = supabase.table('students').select('full_name').eq('id', student_id).execute()
            if st_res.data:
                student_name = st_res.data[0].get('full_name')
        except Exception:
            pass
        if student_name == "Unknown Student":
            try:
                st_fallback = execute_sqlite_query("SELECT full_name FROM students WHERE id = ?", [student_id])
                if st_fallback:
                    student_name = st_fallback[0].get('full_name')
            except Exception:
                pass

        # Lookup teacher/user info
        teacher_name = "Admin"
        faculty_id = None
        user = request.user
        user_email = user.email if user and user.is_authenticated else ""
        if user_email:
            try:
                user_res = supabase.table('users').select('linked_id, name').eq('email', user_email).execute()
                if user_res.data:
                    faculty_id = user_res.data[0].get('linked_id')
                    teacher_name = user_res.data[0].get('name', 'Admin')
            except Exception:
                pass
            if not faculty_id:
                try:
                    user_fallback = execute_sqlite_query("SELECT linked_id, name FROM users WHERE email = ?", [user_email])
                    if user_fallback:
                        faculty_id = user_fallback[0].get('linked_id')
                        teacher_name = user_fallback[0].get('name', 'Admin')
                except Exception:
                    pass

        import uuid
        from django.utils import timezone
        row_id = str(uuid.uuid4())
        today_str = timezone.now().strftime('%Y-%m-%d')

        row = {
            'id': row_id,
            'student_id': student_id,
            'student_name': student_name,
            'faculty_id': faculty_id,
            'teacher_name': teacher_name,
            'action_type': action_type,
            'notes': notes,
            'outcome': outcome,
            'date': today_str,
            'follow_up_date': follow_up_date
        }

        # Try saving to Supabase first
        saved_to_supabase = False
        res_data = None
        try:
            res = supabase.table('interventions').insert(row).execute()
            if res.data:
                res_data = res.data[0]
                saved_to_supabase = True
        except Exception as e:
            print("Supabase error in create intervention, falling back to SQLite:", e)

        # Save to SQLite as fallback or local mirroring (always mirror locally so SQLite stays up to date too!)
        try:
            execute_write_query(
                """INSERT INTO interventions (id, student_id, student_name, faculty_id, teacher_name, action_type, notes, outcome, date, follow_up_date) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [row_id, student_id, student_name, faculty_id, teacher_name, action_type, notes, outcome, today_str, follow_up_date]
            )
            if not saved_to_supabase:
                res_data = row.copy()
        except Exception as sqle:
            print("SQLite error in create intervention:", sqle)
            if not saved_to_supabase:
                return Response({"error": "Failed to save to database: " + str(sqle)}, status=500)

        # Log audit trail
        try:
            audit_id = str(uuid.uuid4())
            audit_details = f"Logged intervention for {student_name}: {action_type}"
            audit_time = timezone.now().isoformat()
            
            try:
                supabase.table('audit_log').insert({
                    'id': audit_id,
                    'action': 'intervention_logged',
                    'user_id': faculty_id or user_email,
                    'details': audit_details,
                    'created_at': audit_time
                }).execute()
            except Exception:
                pass
                
            execute_write_query(
                "INSERT INTO audit_log (id, action, user_id, details, created_at) VALUES (?, ?, ?, ?, ?)",
                [audit_id, 'intervention_logged', faculty_id or user_email, audit_details, audit_time]
            )
        except Exception as ae:
            print("Intervention audit logging failed:", ae)

        # Enrich response
        res_data['id'] = row_id
        res_data['_id'] = row_id
        res_data['student'] = student_id
        res_data['intervention_type'] = action_type
        res_data['intervention_type_display'] = action_type
        res_data['status'] = outcome

        return Response(res_data, status=201)

    def retrieve(self, request, pk=None):
        data = None
        try:
            res = supabase.table('interventions').select('*').eq('id', pk).execute()
            if res.data:
                data = res.data[0]
        except Exception:
            pass
        
        if not data:
            try:
                db_data = execute_sqlite_query("SELECT * FROM interventions WHERE id = ?", [pk])
                if db_data:
                    data = db_data[0]
            except Exception:
                pass
                
        if not data:
            return Response({"error": "Not found"}, status=404)
            
        data['id'] = data.get('id')
        data['_id'] = data.get('id')
        data['student'] = data.get('student_id')
        data['intervention_type'] = data.get('action_type')
        data['intervention_type_display'] = data.get('action_type')
        data['status'] = data.get('outcome')
        return Response(data)

    def update(self, request, pk=None):
        data = request.data
        update_data = {}
        
        if 'intervention_type' in data or 'action_type' in data:
            update_data['action_type'] = data.get('intervention_type') or data.get('action_type')
        if 'status' in data or 'outcome' in data:
            update_data['outcome'] = data.get('status') or data.get('outcome')
        if 'notes' in data:
            update_data['notes'] = data.get('notes')
        if 'follow_up_date' in data:
            update_data['follow_up_date'] = data.get('follow_up_date')
            
        if not update_data:
            return Response({"error": "No fields to update"}, status=400)
            
        res_data = None
        try:
            res = supabase.table('interventions').update(update_data).eq('id', pk).execute()
            if res.data:
                res_data = res.data[0]
        except Exception as e:
            print("Supabase error in update intervention:", e)
            
        try:
            set_clauses = ", ".join([f"{k} = ?" for k in update_data.keys()])
            params = list(update_data.values()) + [pk]
            execute_write_query(
                f"UPDATE interventions SET {set_clauses} WHERE id = ?",
                params
            )
            if not res_data:
                fallback = execute_sqlite_query("SELECT * FROM interventions WHERE id = ?", [pk])
                if fallback:
                    res_data = fallback[0]
        except Exception as sqle:
            print("SQLite error in update intervention:", sqle)
            
        if not res_data:
            return Response({"error": "Intervention not found or update failed"}, status=404)
            
        res_data['id'] = res_data.get('id')
        res_data['_id'] = res_data.get('id')
        res_data['student'] = res_data.get('student_id')
        res_data['intervention_type'] = res_data.get('action_type')
        res_data['intervention_type_display'] = res_data.get('action_type')
        res_data['status'] = res_data.get('outcome')
        return Response(res_data)

    def partial_update(self, request, pk=None):
        return self.update(request, pk)

    def destroy(self, request, pk=None):
        deleted = False
        try:
            supabase.table('interventions').delete().eq('id', pk).execute()
            deleted = True
        except Exception:
            pass
            
        try:
            execute_write_query("DELETE FROM interventions WHERE id = ?", [pk])
            deleted = True
        except Exception:
            pass
            
        return Response(status=204)

    @action(detail=True, methods=['patch', 'post'], url_path='update-outcome')
    def update_outcome(self, request, pk=None):
        outcome = request.data.get('outcome')
        if not outcome:
            return Response({"error": "outcome is required"}, status=400)
            
        res_data = None
        try:
            res = supabase.table('interventions').update({'outcome': outcome}).eq('id', pk).execute()
            if res.data:
                res_data = res.data[0]
        except Exception as e:
            print("Supabase error in update-outcome:", e)
            
        try:
            execute_write_query("UPDATE interventions SET outcome = ? WHERE id = ?", [outcome, pk])
            if not res_data:
                fallback = execute_sqlite_query("SELECT * FROM interventions WHERE id = ?", [pk])
                if fallback:
                    res_data = fallback[0]
        except Exception as sqle:
            print("SQLite error in update-outcome:", sqle)
            
        if not res_data:
            return Response({"error": "Intervention not found"}, status=404)
            
        res_data['id'] = res_data.get('id')
        res_data['_id'] = res_data.get('id')
        res_data['student'] = res_data.get('student_id')
        res_data['intervention_type'] = res_data.get('action_type')
        res_data['intervention_type_display'] = res_data.get('action_type')
        res_data['status'] = res_data.get('outcome')
        return Response(res_data)

    @action(detail=False, methods=['get'], url_path='student/(?P<student_id>[^/.]+)')
    def student_history(self, request, student_id=None):
        data = []
        try:
            res = supabase.table('interventions').select('*').eq('student_id', student_id).order('date', desc=True).execute()
            data = res.data or []
        except Exception as e:
            print("Supabase error in student_history, falling back to SQLite:", e)
            try:
                data = execute_sqlite_query(
                    "SELECT * FROM interventions WHERE student_id = ? ORDER BY date DESC",
                    [student_id]
                )
            except Exception as sqle:
                print("SQLite error in student_history:", sqle)
                
        for row in data:
            row['id'] = row.get('id')
            row['_id'] = row.get('id')
            row['student'] = row.get('student_id')
            row['intervention_type'] = row.get('action_type')
            row['intervention_type_display'] = row.get('action_type')
            row['status'] = row.get('outcome')
            
        return Response(data)
