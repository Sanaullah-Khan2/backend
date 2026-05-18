import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduaims.settings')
import django
django.setup()
from eduaims.supabase_client import supabase

def print_table_info(table_name):
    res = supabase.table(table_name).select('*').limit(1).execute()
    print(f"--- Table: {table_name} ---")
    if res.data:
        print("Columns:", list(res.data[0].keys()))
    else:
        print("No data. Cannot determine columns via REST easily, but table likely exists.")

print_table_info('students')
print_table_info('faculty')
print_table_info('users')
print_table_info('audit_log')
print_table_info('fees')
print_table_info('enrollment_requests')
