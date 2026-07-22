import os
import sys
import django
from django.db import connection

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

def populate_search_vector():
    print("[START] Starting massive SQL update for search_vector...")
    print("This is running directly inside Supabase's PostgreSQL engine (lightning fast).")
    
    with connection.cursor() as cursor:
        # We assign weights: Name (A - highest), City (B), Purpose (C)
        sql = """
        UPDATE companies 
        SET search_vector = 
            setweight(to_tsvector('norwegian', coalesce(name, '')), 'A') || 
            setweight(to_tsvector('norwegian', coalesce(organization_number, '')), 'A') ||
            setweight(to_tsvector('norwegian', coalesce(city, '')), 'B') || 
            setweight(to_tsvector('norwegian', coalesce(business_postal_code, '')), 'B') || 
            setweight(to_tsvector('norwegian', coalesce(purpose, '')), 'C');
        """
        cursor.execute(sql)
        print("[SUCCESS] search_vector column successfully populated for all 1.16 million companies!")

        print("\n[SETUP] Creating automatic PostgreSQL Trigger...")
        trigger_sql = """
        CREATE OR REPLACE FUNCTION update_search_vector_trigger() RETURNS trigger AS $$
        BEGIN
          NEW.search_vector :=
            setweight(to_tsvector('norwegian', coalesce(NEW.name, '')), 'A') ||
            setweight(to_tsvector('norwegian', coalesce(NEW.organization_number, '')), 'A') ||
            setweight(to_tsvector('norwegian', coalesce(NEW.city, '')), 'B') ||
            setweight(to_tsvector('norwegian', coalesce(NEW.business_postal_code, '')), 'B') ||
            setweight(to_tsvector('norwegian', coalesce(NEW.purpose, '')), 'C');
          RETURN NEW;
        END
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS company_search_vector_update ON companies;

        CREATE TRIGGER company_search_vector_update
        BEFORE INSERT OR UPDATE ON companies
        FOR EACH ROW EXECUTE FUNCTION update_search_vector_trigger();
        """
        cursor.execute(trigger_sql)
        print("[SUCCESS] Trigger installed. Future inserts/updates will auto-populate the search_vector!")

if __name__ == '__main__':
    populate_search_vector()
