from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from eduaims.supabase_client import supabase


@api_view(['GET'])
@permission_classes([AllowAny])
def list_assignments(request):
    """List all assignments, optionally filtered by class_name or faculty_id."""
    try:
        query = supabase.table('assignments').select('*').eq('is_active', True).order('created_at', desc=True)
        class_name = request.GET.get('class_name')
        faculty_id = request.GET.get('faculty_id')
        if class_name:
            query = query.eq('class_name', class_name)
        if faculty_id:
            query = query.eq('faculty_id', faculty_id)
        res = query.execute()
        assignments = res.data or []

        # Enrich with submission counts
        for a in assignments:
            subs = supabase.table('assignment_submissions').select('id, status').eq('assignment_id', a['id']).execute().data or []
            a['submitted_count'] = len([s for s in subs if s['status'] == 'submitted'])
            a['late_count'] = len([s for s in subs if s['status'] == 'late'])
            a['pending_count'] = len([s for s in subs if s['status'] == 'pending'])
            a['total_submissions'] = len(subs)

        return Response({"success": True, "data": assignments})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_assignment(request):
    """Create a new assignment."""
    try:
        d = request.data
        new_assignment = {
            'title': d.get('title'),
            'description': d.get('description', ''),
            'class_name': d.get('class_name'),
            'subject': d.get('subject'),
            'faculty_id': d.get('faculty_id'),
            'due_date': d.get('due_date'),
            'total_marks': d.get('total_marks', 100),
            'is_active': True,
        }
        res = supabase.table('assignments').insert(new_assignment).execute()
        if not res.data:
            return Response({"success": False, "error": "Failed to create assignment"}, status=500)

        assignment = res.data[0]

        # Auto-create pending submissions for all students in the class
        students_res = supabase.table('students').select('id, full_name').eq('class_name', d.get('class_name')).eq('is_active', True).execute()
        if students_res.data:
            submissions = []
            for s in students_res.data:
                submissions.append({
                    'assignment_id': assignment['id'],
                    'student_id': s['id'],
                    'student_name': s['full_name'],
                    'status': 'pending'
                })
            if submissions:
                supabase.table('assignment_submissions').insert(submissions).execute()

        return Response({"success": True, "data": assignment}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_assignment(request, assignment_id):
    """Get a single assignment's details."""
    try:
        res = supabase.table('assignments').select('*').eq('id', assignment_id).execute()
        if not res.data:
            return Response({"error": "Assignment not found"}, status=404)
        return Response({"success": True, "data": res.data[0]})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([AllowAny])
def update_assignment(request, assignment_id):
    """Update an assignment."""
    try:
        d = request.data
        update_data = {}
        for field in ['title', 'description', 'class_name', 'subject', 'due_date', 'total_marks']:
            if d.get(field) is not None:
                update_data[field] = d.get(field)
        res = supabase.table('assignments').update(update_data).eq('id', assignment_id).execute()
        return Response({"success": True, "data": res.data[0] if res.data else None})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_assignment(request, assignment_id):
    """Soft delete (deactivate) an assignment."""
    try:
        supabase.table('assignments').update({'is_active': False}).eq('id', assignment_id).execute()
        return Response({"success": True, "message": "Assignment deleted"})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def list_submissions(request, assignment_id):
    """Get all submissions for an assignment."""
    try:
        res = supabase.table('assignment_submissions').select('*').eq('assignment_id', assignment_id).order('created_at', desc=False).execute()
        return Response({"success": True, "data": res.data or []})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([AllowAny])
def update_submission_marks(request, assignment_id, student_id):
    """Enter/update marks and feedback for a student's submission."""
    try:
        d = request.data
        update_data = {
            'marks_obtained': d.get('marks_obtained'),
            'feedback': d.get('feedback', ''),
            'status': 'submitted',
            'submitted_at': timezone.now().isoformat()
        }
        res = supabase.table('assignment_submissions').update(update_data).eq('assignment_id', assignment_id).eq('student_id', student_id).execute()
        if not res.data:
            return Response({"error": "Submission not found"}, status=404)
        return Response({"success": True, "data": res.data[0]})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
