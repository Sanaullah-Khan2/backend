import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduaims.settings')
django.setup()

from apps.students.models import Student
from apps.faculty.models import FacultyClass
from apps.auth_app.views import get_sb

sb = get_sb()

print('Wiping all data from Supabase and Django DB...')
# Delete all non-admin users in supabase
users_res = sb.table('users').select('id, role, email').execute()
for u in users_res.data:
    if u['email'] != 'sanaullahkkhan2004@gmail.com':
        sb.table('users').delete().eq('id', u['id']).execute()

# Clear Django ORM tables
Student.objects.all().delete()
FacultyClass.objects.all().delete()

# Try clearing other tables directly in supabase just in case
try:
    sb.table('students').delete().neq('id', 'dummy').execute()
except: pass

try:
    sb.table('faculty_classes').delete().neq('id', 'dummy').execute()
except: pass

print('Data completely wiped. Only the primary admin remains.')
