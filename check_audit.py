import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduaims.settings')
import django
django.setup()
from eduaims.supabase_client import supabase

# Check audit_log columns by fetching one row
res = supabase.table('audit_log').select('*').limit(1).execute()
print("audit_log data:", res.data)
if res.data:
    print("audit_log columns:", list(res.data[0].keys()))
else:
    print("No data in audit_log, let's check the table exists")
    # Try inserting a test record with minimal fields
    try:
        test = supabase.table('audit_log').insert({'action': 'test'}).execute()
        print("Insert with just 'action' worked:", test.data)
        if test.data:
            print("Columns:", list(test.data[0].keys()))
            # Delete test record
            supabase.table('audit_log').delete().eq('id', test.data[0]['id']).execute()
    except Exception as e:
        print("Insert error:", e)
