import os
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from supabase import create_client
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .serializers import CustomTokenObtainPairSerializer, UserSerializer

User = get_user_model()

from rest_framework_simplejwt.tokens import RefreshToken
def generate_tokens_for_user(user_dict):
    django_user, _ = get_user_model().objects.get_or_create(
        email=user_dict['email'],
        defaults={'role': user_dict['role'], 'name': user_dict.get('name', '')}
    )
    refresh = RefreshToken.for_user(django_user)
    refresh['email'] = user_dict['email']
    refresh['role'] = user_dict['role']
    
    access = refresh.access_token
    access['email'] = user_dict['email']
    access['role'] = user_dict['role']
    
    return {
        'access': str(access),
        'refresh': str(refresh)
    }

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')
        
        sb = get_sb()
        result = sb.table('users').select('*').eq('email', email).execute()
        if not result.data:
            return Response({'error': 'Invalid email or password.'}, status=401)
            
        user = result.data[0]
        
        import hashlib
        salt = 'eduaims_fixed_salt_2024'
        expected = hashlib.sha256((salt + password).encode()).hexdigest()
        if user['password_hash'] != expected:
            return Response({'error': 'Invalid email or password.'}, status=401)

        # Check if user is active
        if not user.get('is_active', True):
            return Response({
                'error': 'pending_approval', 
                'message': 'Your account is pending admin approval'
            }, status=403)

        # If it's an admin login, we verify role from DB
        if user['role'] == 'admin':
            if not user.get('is_active', True):
                return Response({'error': 'Access denied'}, status=403)
        # Note: We allow non-admins to login here since they need tokens for other portals

        tokens = generate_tokens_for_user(user)
        return Response({
            'access': tokens['access'],
            'refresh': tokens['refresh']
        })

class UserMeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

def get_sb():
    return create_client(os.getenv('SUPABASE_URL', ''), os.getenv('SUPABASE_SERVICE_KEY', ''))

@api_view(['GET'])
@permission_classes([AllowAny])
def audit_log(request):
    try:
        sb = get_sb()
        result = sb.table('audit_log').select('*').order('created_at', desc=True).limit(100).execute()
        return Response({"success": True, "data": result.data, "count": len(result.data)})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def list_users(request):
    try:
        sb = get_sb()
        result = sb.table('users').select('id,email,role,name,is_active,created_at').execute()
        return Response({"success": True, "data": result.data, "count": len(result.data)})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def deactivate_user(request, user_id):
    try:
        sb = get_sb()
        result = sb.table('users').update({'is_active': False}).eq('id', user_id).execute()
        return Response({"success": True, "message": "User deactivated"})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def school_profile(request):
    try:
        data = {
            "school_name": "HITEC University",
            "address": "Taxila Cantt, Pakistan", 
            "contact": "+92-51-9047540",
            "email": "info@hitecuni.edu.pk"
        }
        return Response({"success": True, "data": data})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_admin_view(request):
    user = request.user
    
    # We must check if the requesting user is an admin by querying their role from DB or JWT
    # SimpleJWT token payload doesn't map to request.user.role directly if not customized properly
    # Let's verify from Supabase to be completely safe
    sb = get_sb()
    req_user_res = sb.table('users').select('role, id').eq('email', user.email).execute()
    if not req_user_res.data or req_user_res.data[0]['role'] != 'admin':
        return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)
    
    requesting_admin_id = req_user_res.data[0]['id']
    
    data = request.data
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    name = data.get('name', '')

    if not email or not password or not name:
        return Response({"error": "Name, email, and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    # Check if email exists
    existing = sb.table('users').select('id').eq('email', email).execute()
    if existing.data:
        return Response({"error": "This email is already registered"}, status=status.HTTP_409_CONFLICT)

    import hashlib
    import datetime
    salt = 'eduaims_fixed_salt_2024'
    password_hash = hashlib.sha256((salt + password).encode()).hexdigest()

    try:
        # Insert new admin
        new_admin = {
            'email': email,
            'password_hash': password_hash,
            'role': 'admin',
            'name': name,
            'is_active': True
        }
        res = sb.table('users').insert(new_admin).execute()
        
        if res.data:
            new_id = res.data[0]['id']
            # Log to audit_log
            audit_entry = {
                'action': 'admin_created',
                'user_id': requesting_admin_id,
                'details': f'Created new admin: {email}'
            }
            sb.table('audit_log').insert(audit_entry).execute()
            
            return Response({"success": True, "message": f"Admin account created for {email}"})
        else:
            return Response({"error": "Failed to create admin"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_user_view(request):
    user = request.user
    if getattr(user, 'role', '') != 'admin':
        return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)
    
    data = request.data
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    role = data.get('role')

    if role == 'admin' and user.email != 'sanaullahkkhan2004@gmail.com':
        return Response({"error": "Only the primary admin can create admin accounts"}, status=status.HTTP_403_FORBIDDEN)

    try:
        new_user = get_user_model().objects.create_user(
            email=email,
            password=password,
            name=name,
            role=role
        )
        return Response({"success": True, "message": f"Account created! Credentials sent to {email}"})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    import hashlib
    email    = request.data.get('email', '').lower().strip()
    password = request.data.get('password', '')
    name     = request.data.get('name', '')
    role     = request.data.get('role', '')

    if not all([email, password, name, role]):
        return Response({'error': 'Name, email, password and role are required.'}, status=400)
    if role == 'admin':
        return Response({'error': 'Admin accounts cannot be self-registered.'}, status=403)
    if role not in ['teacher', 'student', 'parent']:
        return Response({'error': 'Invalid role selected.'}, status=400)
    if len(password) < 6:
        return Response({'error': 'Password must be at least 6 characters.'}, status=400)

    try:
        sb = get_sb()
        existing = sb.table('users').select('id').eq('email', email).execute()
        if existing.data:
            return Response({'error': 'An account with this email already exists. Please sign in.'}, status=409)

        salt = 'eduaims_fixed_salt_2024'
        password_hash = hashlib.sha256((salt + password).encode()).hexdigest()

        user_doc = {
            'email':         email,
            'password_hash': password_hash,
            'role':          role,
            'name':          name,
            'is_active':     True,
        }
        result = sb.table('users').insert(user_doc).execute()
        if not result.data:
            return Response({'error': 'Failed to create account. Try again.'}, status=500)

        new_user = result.data[0]
        tokens = generate_tokens_for_user(new_user)

        return Response({
            'success': True,
            'message': 'Account created successfully!',
            'access':  tokens['access'],
            'refresh': tokens['refresh'],
            'user': {
                'id':    str(new_user['id']),
                'email': email,
                'name':  name,
                'role':  role,
            }
        }, status=201)

    except Exception as e:
        return Response({'error': str(e)}, status=500)
