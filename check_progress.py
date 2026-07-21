import os
import sys
import django
from django.db import connection

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

def get_count(table_name):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]

print("--- SUPABASE IMPORT PROGRESS ---")
tables = ['companies', 'financial_statements', 'people', 'company_roles', 'company_locations', 'company_industries']
for table in tables:
    try:
        count = get_count(table)
        print(f"{table.ljust(25)}: {count:,} rows")
    except Exception as e:
        print(f"{table.ljust(25)}: 0 rows (or not found)")
