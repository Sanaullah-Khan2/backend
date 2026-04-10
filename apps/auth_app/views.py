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

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

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
