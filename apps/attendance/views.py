from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import AttendanceRecord
from .serializers import AttendanceRecordSerializer
from apps.students.models import Student
from datetime import datetime

class AttendanceViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='mark')
    def mark_attendance(self, request):
        from eduaims.supabase_client import supabase
        from apps.ai_engine.scoring import compute_features
        from apps.ai_engine.risk_engine import calculate_risk_score

        date_str = request.data.get('date')
        subject_id = request.data.get('subject_id', '')
        records = request.data.get('records', [])
        
        if not date_str or not records:
            return Response({"error": "date and records are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        marked_by = str(request.user.id) if hasattr(request.user, 'id') else None
        created_records = []
        
        for record_data in records:
            student_id = record_data.get('student_id')
            att_status = record_data.get('status')
            try:
                existing = supabase.table('attendance').select('id').eq('student_id', student_id).eq('date', date_str).eq('subject_id', subject_id).execute()
                att_data = {
                    'student_id': student_id,
                    'date': date_str,
                    'subject_id': subject_id,
                    'status': att_status,
                    'marked_by': marked_by
                }
                
                if existing.data:
                    res = supabase.table('attendance').update(att_data).eq('id', existing.data[0]['id']).execute()
                else:
                    res = supabase.table('attendance').insert(att_data).execute()
                    
                if res.data:
                    created_records.append(res.data[0])
                    
                    # Update AI Risk Score for this student
                    try:
                        features = compute_features(student_id)
                        calc_score, level, reason = calculate_risk_score(
                            attendance_pct=features['attendance_pct'],
                            grade_avg=features['grade_avg'],
                            grade_trend=0,
                            fee_default=0,
                            behavior_count=features['assignments_missed']
                        )
                        risk_data = {
                            'student_id': student_id,
                            'score': calc_score,
                            'risk_level': level.lower(),
                            'attendance_pct': features['attendance_pct'],
                            'grade_avg': features['grade_avg'],
                            'assignments_missed': features['assignments_missed'],
                            'top_factors': [reason]
                        }
                        supabase.table('risk_scores').insert(risk_data).execute()
                    except Exception as ai_err:
                        print("AI scoring err:", ai_err)
            except Exception as e:
                print("Attendance error:", e)
                continue

        return Response({"message": "Attendance marked", "records": created_records}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='student/(?P<student_id>[^/.]+)')
    def student_attendance(self, request, student_id=None):
        from eduaims.supabase_client import supabase
        try:
            res = supabase.table('attendance').select('*').eq('student_id', student_id).order('date', desc=True).execute()
            return Response(res.data or [])
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    @action(detail=False, methods=['get'], url_path='class/(?P<class_id>[^/.]+)/date/(?P<date_str>[^/.]+)')
    def class_attendance(self, request, class_id=None, date_str=None):
        from eduaims.supabase_client import supabase
        try:
            students_res = supabase.table('students').select('*').eq('class_id', class_id).execute()
            students = students_res.data or []
            
            student_ids = [s['id'] for s in students]
            if not student_ids:
                return Response([])
                
            att_res = supabase.table('attendance').select('*').in_('student_id', student_ids).eq('date', date_str).execute()
            records = att_res.data or []
            record_map = {r['student_id']: r for r in records}
            
            response_data = []
            for s in students:
                s_id = s['id']
                if s_id in record_map:
                    response_data.append(record_map[s_id])
                else:
                    response_data.append({
                        "student_id": s_id,
                        "student_name": s.get('full_name'),
                        "student_registration_no": s.get('registration_no'),
                        "status": None
                    })
            return Response(response_data)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
