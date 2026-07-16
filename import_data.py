# python import_data.py - to run this



import os
import sys
import pandas as pd
from sqlalchemy import create_engine
import django

# 1. Setup the Django Environment so we can securely access your config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from backend.config import settings

# 2. Fix the Supabase URL for SQLAlchemy (SQLAlchemy strictly requires 'postgresql://')
db_url = settings.db_url.get_secret_value()
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(db_url)

# The path to your Data Engineering folder
DATA_DIR = 'E:/Alura/ASData/Data Exploraton'

def import_table(csv_name, table_name, columns=None, transform_func=None):
    print(f"Loading {csv_name} into {table_name}...")
    file_path = os.path.join(DATA_DIR, csv_name)
    
    # Read everything as text initially to prevent Pandas from making bad guesses
    df = pd.read_csv(file_path, dtype=str) 
    
    # Apply any custom cleanup rules
    if transform_func:
        df = transform_func(df)
        
    # Drop any extra columns we don't need in the final database
    if columns:
        # Only keep columns that actually exist in the dataframe
        valid_cols = [c for c in columns if c in df.columns]
        df = df[valid_cols]
        
    # Postgres/Supabase Optimization: method='multi' does massive Bulk Inserts instead of row-by-row
    df.to_sql(table_name, engine, if_exists='append', index=False, chunksize=2000, method='multi')
    print(f"✅ {csv_name} imported successfully ({len(df)} rows).")


print("\n🚀 STARTING MASSIVE DATA IMPORT TO SUPABASE...\n")

# STEP 1: Dictionaries (No Foreign Key dependencies)
import_table('industries.csv', 'industries')
import_table('municipalities.csv', 'municipalities')
import_table('organization_types.csv', 'organization_types')
import_table('role_types.csv', 'role_types')

# STEP 2: Core Companies Table
# We explicitly list ONLY the columns that belong in the companies table, stripping out the rest.
company_cols = [
    'organization_number', 'name', 'organization_type_code', 'established_date', 
    'registered_date', 'employee_count', 'website', 'business_address', 
    'business_postal_code', 'business_city', 'business_country_code', 
    'postal_address', 'postal_code', 'city', 'country_code', 
    'institutional_sector_code', 'institutional_sector_name', 
    'is_vat_registered', 'is_registered_business_register', 
    'is_bankrupt', 'is_under_liquidation', 'purpose'
]
import_table('golden_100k_transformed.csv', 'companies', columns=company_cols)

# STEP 3: Child Data (Must be done after Companies)
import_table('company_locations.csv', 'company_locations')

# We must strip out the 'NO_DATA' marker rows we used for the scraper's auto-resume feature
def clean_financials(df):
    return df[df['financial_year'] != 'NO_DATA']

import_table('financial_statements.csv', 'financial_statements', transform_func=clean_financials)

# STEP 4: People and Roles
import_table('people.csv', 'people')
# (We already renamed 'organization_number' to 'company_id' in company_roles.csv earlier!)
import_table('company_roles.csv', 'company_roles')

# STEP 5: Junction Tables
def rename_org_to_company(df):
    return df.rename(columns={'organization_number': 'company_id'})

import_table('company_industries.csv', 'company_industries', transform_func=rename_org_to_company)

print("\n🎉 ALL DATA IMPORTED SUCCESSFULLY! THE SEARCH ENGINE IS READY!")



