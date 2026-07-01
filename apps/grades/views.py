from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Grade
from .serializers import GradeSerializer
from apps.students.models import Student

class GradeViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request):
        """Handle POST /api/grades/ from the teacher grades page.
        Accepts: { grades: [{ student_id, subject, exam_type, marks, total_marks, month, class_name }] }
        """
        from eduaims.supabase_client import supabase

        grades_list = request.data.get('grades', [])
        if not grades_list:
            return Response({"error": "grades array is required"}, status=status.HTTP_400_BAD_REQUEST)

        recorded_by = str(request.user.id) if hasattr(request.user, 'id') else None
        created = []

        for g in grades_list:
            student_id = g.get('student_id')
            subject_id = g.get('subject') or g.get('subject_id', '')
            term = g.get('exam_type') or g.get('term', '')
            score = g.get('marks', 0)
            if score == '' or score is None:
                score = 0
            total_score = g.get('total_marks', 100)

            try:
                # Check for existing record
                existing = supabase.table('grades').select('id') \
                    .eq('student_id', student_id) \
                    .eq('subject_id', subject_id) \
                    .eq('term', term).execute()

                grade_data = {
                    'student_id': student_id,
                    'subject_id': subject_id,
                    'term': term,
                    'score': float(score),
                    'total_score': float(total_score),
                    'recorded_by': recorded_by
                }

                if existing.data:
                    res = supabase.table('grades').update(grade_data).eq('id', existing.data[0]['id']).execute()
                else:
                    res = supabase.table('grades').insert(grade_data).execute()

                if res.data:
                    created.append(res.data[0])
            except Exception as e:
                print(f"Grade save error for student {student_id}:", e)
                continue

        return Response({"message": "Grades saved", "count": len(created), "records": created}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='bulk-mark')
    def bulk_mark(self, request):
        from eduaims.supabase_client import supabase
        from apps.ai_engine.scoring import compute_features
        from apps.ai_engine.risk_engine import calculate_risk_score

        subject_id = request.data.get('subject_id')
        term = request.data.get('term')
        records = request.data.get('records', [])
        
        if not subject_id or not term or not records:
            return Response({"error": "subject_id, term, and records are required"}, status=status.HTTP_400_BAD_REQUEST)
            
        recorded_by = str(request.user.id) if hasattr(request.user, 'id') else None
        created_records = []
        
        for record_data in records:
            student_id = record_data.get('student_id')
            score = record_data.get('score')
            total_score = record_data.get('total_score', 100.00)
            
            try:
                # Check if exists
                existing = supabase.table('grades').select('id').eq('student_id', student_id).eq('subject_id', subject_id).eq('term', term).execute()
                grade_data = {
                    'student_id': student_id,
                    'subject_id': subject_id,
                    'term': term,
                    'score': score,
                    'total_score': total_score,
                    'recorded_by': recorded_by
                }
                
                if existing.data:
                    res = supabase.table('grades').update(grade_data).eq('id', existing.data[0]['id']).execute()
                else:
                    res = supabase.table('grades').insert(grade_data).execute()
                    
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
                print("Grades error:", e)
                continue

        return Response({"message": "Grades saved", "records": created_records}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='student/(?P<student_id>[^/.]+)')
    def student_grades(self, request, student_id=None):
        from eduaims.supabase_client import supabase
        try:
            res = supabase.table('grades').select('*').eq('student_id', student_id).execute()
            return Response(res.data or [])
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    @action(detail=False, methods=['get'], url_path='class/(?P<class_id>[^/.]+)/subject/(?P<subject_id>[^/.]+)/term/(?P<term>[^/.]+)')
    def class_grades(self, request, class_id=None, subject_id=None, term=None):
        from eduaims.supabase_client import supabase
        try:
            students_res = supabase.table('students').select('*').eq('class_id', class_id).execute()
            students = students_res.data or []
            
            student_ids = [s['id'] for s in students]
            if not student_ids:
                return Response([])
                
            grades_res = supabase.table('grades').select('*').in_('student_id', student_ids).eq('subject_id', subject_id).eq('term', term).execute()
            records = grades_res.data or []
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
                        "score": "",
                        "total_score": 100.00
                    })
            return Response(response_data)
        except Exception as e:
            return Response({"error": str(e)}, status=500)
