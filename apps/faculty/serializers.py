from rest_framework import serializers
from .models import Faculty
from django.contrib.auth import get_user_model
import random
import string

User = get_user_model()

class FacultySerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, write_only=True)

    class Meta:
        model = Faculty
        fields = ('_id', 'employee_id', 'full_name', 'subject_specialization', 'contact_number', 'classes_assigned', 'joined_date', 'is_active', 'email', 'role')
        read_only_fields = ('_id', 'employee_id', 'joined_date')

    def create(self, validated_data):
        email = validated_data.pop('email')
        role = validated_data.pop('role')
        
        # Generate random password
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        
        # Create User
        user = User.objects.create_user(
            email=email,
            password=password,
            name=validated_data.get('full_name'),
            role=role,
            is_staff=(role in ['admin', 'teacher'])
        )
        
        # In a real system, we'd send an email here using Django's send_mail
        print(f"--- MOCK EMAIL SENDER ---")
        print(f"To: {email}")
        print(f"Subject: Welcome to EduAIMS Dashboard")
        print(f"Body: Your account has been created. Role: {role}, Password: {password}")
        print(f"-------------------------")

        # Create Faculty
        faculty = Faculty.objects.create(user=user, **validated_data)
        
        # Update user linked_id back-reference to Faculty profile
        user.linked_id = faculty._id
        user.save()
        
        return faculty
