# python import_data.py - to run this

import os
import sys
import pandas as pd
from sqlalchemy import create_engine, text
import django

# 1. Setup the Django Environment so we can securely access your config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from backend.config import settings
import json

# 2. Fix the Supabase URL for SQLAlchemy (SQLAlchemy strictly requires 'postgresql://')
db_url = settings.db_url.get_secret_value()
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(db_url)

# The path to your Data Engineering folder
DATA_DIR = 'E:/Alura/ASData/Data Exploraton'

def import_table(csv_name, table_name, columns=None, transform_func=None):
    print(f"Loading {csv_name} into {table_name}...")
    with engine.connect() as conn:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        if count > 0:
            print(f"⚠️ {table_name} already has {count} rows. Skipping import to prevent duplicates.")
            return

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
        
    # Insert data using default Pandas executemany (safer for Supabase parameter limits)
    df.to_sql(table_name, engine, if_exists='append', index=False, chunksize=500)
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
    'is_bankrupt', 'is_under_liquidation', 'purpose',
    'is_registered_foundation', 'is_registered_voluntary', 'is_under_forced_liquidation'
]

def transform_companies(df):
    for col in ['business_address', 'postal_address']:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: json.dumps([x]) if pd.notna(x) and str(x).strip() else None)
            
    # Add missing boolean columns that have NOT NULL constraints but no DB-level default
    for col in ['is_registered_foundation', 'is_registered_voluntary', 'is_under_forced_liquidation']:
        if col not in df.columns:
            df[col] = False
            
    # Also fix boolean columns that might be string 'True'/'False' or missing
    bool_cols = [
        'is_vat_registered', 'is_registered_business_register', 
        'is_bankrupt', 'is_under_liquidation'
    ]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].map({'True': True, 'False': False, 'true': True, 'false': False, True: True, False: False}).fillna(False)
            
    return df

import_table('golden_100k_transformed.csv', 'companies', columns=company_cols, transform_func=transform_companies)

# STEP 3: Child Data (Must be done after Companies)
def transform_locations(df):
    if 'organization_number' in df.columns:
        df = df.drop_duplicates(subset=['organization_number'])
    if 'employee_count' in df.columns:
        df['employee_count'] = pd.to_numeric(df['employee_count'], errors='coerce').astype('Int64')
    for col in ['business_address', 'postal_address']:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: json.dumps([x]) if pd.notna(x) and str(x).strip() else None)
    return df

import_table('company_locations.csv', 'company_locations', transform_func=transform_locations)

# We must strip out the 'NO_DATA' marker rows we used for the scraper's auto-resume feature
def clean_financials(df):
    # 'NO_DATA' could be in either column depending on how it was saved
    df = df[(df['financial_year'] != 'NO_DATA') & (df['journal_number'] != 'NO_DATA')].copy()
    df = df.dropna(subset=['financial_year'])
    for col in ['is_liquidation_statement', 'is_small_business', 'audit_exempt']:
        if col not in df.columns:
            df[col] = False
        else:
            df[col] = df[col].map({'True': True, 'False': False, 'true': True, 'false': False, True: True, False: False}).fillna(False)
            
    # Fix float strings being inserted into bigint columns
    money_cols = ['total_assets', 'total_equity', 'operating_revenue', 'operating_profit', 'net_profit']
    for col in money_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
            
    # Also fix financial_year and journal_number being swapped or floats
    for col in ['financial_year', 'journal_number']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
            
    return df

import_table('financial_statements.csv', 'financial_statements', transform_func=clean_financials)

# STEP 4: People and Roles
def transform_people(df):
    if 'id' in df.columns:
        df = df.drop_duplicates(subset=['id'])
    if 'is_deceased' not in df.columns:
        df['is_deceased'] = False
    else:
        df['is_deceased'] = df['is_deceased'].map({'True': True, 'False': False, 'true': True, 'false': False, True: True, False: False}).fillna(False)
    return df

import_table('people.csv', 'people', transform_func=transform_people)

# Fetch valid IDs for foreign key validation
try:
    with engine.connect() as conn:
        VALID_PERSON_IDS = set(row[0] for row in conn.execute(text("SELECT id FROM people")).fetchall())
        VALID_COMPANY_IDS = set(row[0] for row in conn.execute(text("SELECT organization_number FROM companies")).fetchall())
except Exception:
    VALID_PERSON_IDS = set()
    VALID_COMPANY_IDS = set()

def transform_roles(df):
    if 'id' in df.columns:
        df = df.drop_duplicates(subset=['id'])
    for col in ['person_id', 'holding_company_id']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
            
    # Filter out foreign keys that don't exist in the database
    if 'person_id' in df.columns and VALID_PERSON_IDS:
        df = df[df['person_id'].isna() | df['person_id'].isin(VALID_PERSON_IDS)]
    if 'company_id' in df.columns and VALID_COMPANY_IDS:
        df = df[df['company_id'].isna() | df['company_id'].isin(VALID_COMPANY_IDS)]
    if 'holding_company_id' in df.columns and VALID_COMPANY_IDS:
        df = df[df['holding_company_id'].isna() | df['holding_company_id'].isin(VALID_COMPANY_IDS)]
        
    if 'is_active' not in df.columns:
        df['is_active'] = True
    else:
        df['is_active'] = df['is_active'].map({'True': True, 'False': False, 'true': True, 'false': False, True: True, False: False}).fillna(True)
    return df

import_table('company_roles.csv', 'company_roles', transform_func=transform_roles)

# STEP 5: Junction Tables
def rename_org_to_company(df):
    df = df.rename(columns={'organization_number': 'company_id'})
    if 'is_primary' not in df.columns:
        df['is_primary'] = False
    else:
        df['is_primary'] = df['is_primary'].map({'True': True, 'False': False, 'true': True, 'false': False, True: True, False: False}).fillna(False)
    return df

def transform_company_industries(df):
    df = rename_org_to_company(df)
    if 'industry_code' in df.columns:
        df = df.rename(columns={'industry_code': 'industry_id'})
    # Deduplicate company_industries to avoid unique constraint violations
    if 'company_id' in df.columns and 'industry_id' in df.columns:
        df = df.drop_duplicates(subset=['company_id', 'industry_id'])
    return df

import_table('company_industries.csv', 'company_industries', transform_func=transform_company_industries)

print("\n CONGO KING! I have pushed all the .csv to DB just like she did to you from her life.")
