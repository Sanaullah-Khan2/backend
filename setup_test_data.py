import os, sys, django, datetime
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduaims.settings')
django.setup()

from apps.students.models import Student
from django.contrib.auth import get_user_model
from apps.auth_app.views import get_sb
import hashlib

sb = get_sb()

print('Cleaning up non-admin users and dummy students...')
users_res = sb.table('users').select('id, role, email').execute()
for u in users_res.data:
    if u['role'] != 'admin' and u['email'] != 'sanaullahkkhan2004@gmail.com':
        sb.table('users').delete().eq('id', u['id']).execute()

Student.objects.all().delete()

salt = 'eduaims_fixed_salt_2024'
password = 'password123'
password_hash = hashlib.sha256((salt + password).encode()).hexdigest()

teacher_doc = {
    'email': 'teacher@test.com',
    'password_hash': password_hash,
    'role': 'teacher',
    'name': 'Test Teacher',
    'is_active': True,
}
res = sb.table('users').insert(teacher_doc).execute()

students_data = [
    {
        'email': 'student1@test.com',
        'password_hash': password_hash,
        'role': 'student',
        'name': 'Alice Smith',
        'is_active': True,
    },
    {
        'email': 'student2@test.com',
        'password_hash': password_hash,
        'role': 'student',
        'name': 'Bob Johnson',
        'is_active': True,
    },
    {
        'email': 'student3@test.com',
        'password_hash': password_hash,
        'role': 'student',
        'name': 'Charlie Davis',
        'is_active': True,
    }
]

created_students = []
for s in students_data:
    r = sb.table('users').insert(s).execute()
    created_students.append(r.data[0])

dob_date = datetime.date(2010, 1, 1)
for i, s in enumerate(created_students):
    Student.objects.create(
        full_name=s['name'],
        email=s['email'],
        class_id='9',
        section='A',
        registration_no=f'REG-2026-00{i+1}',
        parent_email=f'parent{i+1}@test.com',
        parent_contact='555-010'+str(i),
        dob=dob_date
    )

print('Successfully created Teacher (teacher@test.com / password123) and 3 Students in Class 9-A.')
