from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta
import os

# Supabase client
from supabase import create_client
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY', '')

def get_sb():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ── GET /api/ai/risk-scores/ ──────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def all_risk_scores(request):
    try:
        sb = get_sb()

        # Fetch latest risk score per student
        scores = sb.table('risk_scores')\
            .select('*')\
            .order('calculated_at', desc=True)\
            .execute().data

        # Fetch all students
        students = sb.table('students')\
            .select('id, full_name, class_name')\
            .eq('is_active', True)\
            .execute().data

        # Map students by id
        student_map = {s['id']: s for s in students}

        # Keep only latest score per student
        seen = set()
        result = []
        for score in scores:
            sid = score['student_id']
            if sid in seen:
                continue
            seen.add(sid)
            student = student_map.get(sid, {})
            result.append({
                'student_id':   sid,
                'student_name': student.get('full_name', 'Unknown'),
                'class_name':   student.get('class_name', ''),
                'score':        round(score.get('score', 0)),
                'level':        score.get('level', 'green'),
                'reason':       score.get('reason', ''),
                'calculated_at': str(score.get('calculated_at', ''))[:10],
            })

        # Filter by class if query param given
        class_filter = request.GET.get('class_name')
        if class_filter:
            result = [r for r in result if r['class_name'] == class_filter]

        return Response({
            'success': True,
            'data':    result,
            'count':   len(result),
        })

    except Exception as e:
        return Response({'success': False, 'error': str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ── GET /api/ai/risk-scores/{student_id}/ ────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def student_risk_score(request, student_id):
    try:
        sb = get_sb()

        # Get student info
        student = sb.table('students')\
            .select('id, full_name, class_name')\
            .eq('id', student_id)\
            .single()\
            .execute().data

        if not student:
            return Response({'success': False, 'error': 'Student not found'},
                            status=status.HTTP_404_NOT_FOUND)

        # Get last 5 risk scores (trend)
        scores = sb.table('risk_scores')\
            .select('score, level, reason, calculated_at')\
            .eq('student_id', student_id)\
            .order('calculated_at', desc=True)\
            .limit(5)\
            .execute().data

        latest = scores[0] if scores else {}
        trend  = [{'score': round(s['score']),
                   'date':  str(s['calculated_at'])[:10]} for s in scores]

        return Response({
            'success': True,
            'data': {
                'student_id':   student_id,
                'student_name': student['full_name'],
                'class_name':   student['class_name'],
                'score':        round(latest.get('score', 0)),
                'level':        latest.get('level', 'green'),
                'reason':       latest.get('reason', ''),
                'calculated_at': str(latest.get('calculated_at', ''))[:10],
                'trend':        trend,
            }
        })

    except Exception as e:
        return Response({'success': False, 'error': str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ── POST /api/ai/recalculate/ ─────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def recalculate_all(request):
    try:
        sb = get_sb()
        today = datetime.utcnow().strftime('%Y-%m-%d')
        this_month = datetime.utcnow().strftime('%Y-%m')
        last_month = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m')

        students = sb.table('students')\
            .select('id, full_name, class_name')\
            .eq('is_active', True)\
            .execute().data

        count = 0
        for student in students:
            sid = student['id']

            # Attendance this month
            att = sb.table('attendance')\
                .select('status')\
                .eq('student_id', sid)\
                .gte('date', this_month + '-01')\
                .execute().data
            total  = len(att)
            present = sum(1 for a in att if a['status'] == 'present')
            attendance_pct = (present / total * 100) if total > 0 else 100

            # Grade avg this month
            grades_now = sb.table('grades')\
                .select('percentage')\
                .eq('student_id', sid)\
                .eq('month', this_month)\
                .execute().data
            grade_avg = sum(g['percentage'] for g in grades_now) / len(grades_now) \
                        if grades_now else 100

            # Grade avg last month
            grades_last = sb.table('grades')\
                .select('percentage')\
                .eq('student_id', sid)\
                .eq('month', last_month)\
                .execute().data
            last_avg = sum(g['percentage'] for g in grades_last) / len(grades_last) \
                       if grades_last else grade_avg
            grade_trend = grade_avg - last_avg

            # Risk score formula
            score = 0
            if attendance_pct < 75:  score += 40
            if grade_avg < 50:       score += 35
            if grade_trend < -15:    score += 25
            score = min(score, 100)

            if score >= 70:
                level  = 'red'
                reason = f'Low attendance ({attendance_pct:.0f}%) and poor grades'
            elif score >= 40:
                level  = 'yellow'
                if attendance_pct < 75:
                    reason = f'Low attendance ({attendance_pct:.0f}%)'
                else:
                    reason = f'Grade dropped {abs(grade_trend):.0f}% from last month'
            else:
                level  = 'green'
                reason = 'Student performing well'

            sb.table('risk_scores').insert({
                'student_id':     sid,
                'score':          score,
                'level':          level,
                'reason':         reason,
                'attendance_pct': attendance_pct,
                'grade_avg':      grade_avg,
                'grade_trend':    grade_trend,
                'calculated_at':  today,
            }).execute()
            count += 1

        return Response({'success': True, 'recalculated': count})

    except Exception as e:
        return Response({'success': False, 'error': str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ── GET /api/ai/interventions/ ────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def list_interventions(request):
    try:
        sb = get_sb()
        data = sb.table('interventions')\
            .select('*')\
            .order('date', desc=True)\
            .execute().data
        return Response({'success': True, 'data': data, 'count': len(data)})
    except Exception as e:
        return Response({'success': False, 'error': str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ── POST /api/ai/interventions/ ───────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def create_intervention(request):
    try:
        sb  = get_sb()
        d   = request.data
        today = datetime.utcnow().strftime('%Y-%m-%d')

        row = {
            'student_id':  d.get('student_id'),
            'teacher_id':  d.get('teacher_id'),
            'action_type': d.get('action_type'),
            'notes':       d.get('notes', ''),
            'outcome':     d.get('outcome', 'no_change'),
            'date':        today,
        }
        result = sb.table('interventions').insert(row).execute()
        return Response({'success': True, 'data': result.data},
                        status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'success': False, 'error': str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)