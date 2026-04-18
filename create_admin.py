import os, sys, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduaims.settings')
import django
django.setup()

from supabase import create_client
sb = create_client(
    os.getenv('SUPABASE_URL', ''),
    os.getenv('SUPABASE_SERVICE_KEY', '')
)

salt = 'eduaims_fixed_salt_2024'
password_hash = hashlib.sha256((salt + 'Pak_1947').encode()).hexdigest()

sb.table('users').delete().eq('email', 'sanaullahkkhan2004@gmail.com').execute()

result = sb.table('users').insert({
    'email':         'sanaullahkkhan2004@gmail.com',
    'password_hash': password_hash,
    'role':          'admin',
    'name':          'Sana Ullah Khan',
    'is_active':     True,
}).execute()

if result.data:
    print('Admin created successfully.')
    print('Email   : sanaullahkkhan2004@gmail.com')
    print('Password: Pak_1947')
else:
    print('FAILED to create admin.')
