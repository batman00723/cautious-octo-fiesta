import os
import sys
import django
import time
from django.db import connection

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

org_number = '810034882'

sql = """
EXPLAIN ANALYZE
SELECT 
    c.organization_number,
    c.name,
    ot.description as organization_type,
    c.established_date,
    c.registered_date,
    c.employee_count,
    c.website,
    c.business_address,
    c.business_postal_code,
    c.business_city,
    c.business_country_code,
    c.purpose,
    c.is_vat_registered,
    c.is_bankrupt,
    c.is_under_liquidation,
    (
        SELECT jsonb_agg(jsonb_build_object(
            'code', i.code,
            'description', i.description,
            'is_primary', ci.is_primary
        ))
        FROM company_industries ci
        JOIN industries i ON ci.industry_id = i.code
        WHERE ci.company_id = c.organization_number
    ) as industries,
    (
        SELECT jsonb_agg(jsonb_build_object(
            'financial_year', f.financial_year,
            'operating_revenue', f.operating_revenue,
            'operating_profit', f.operating_profit,
            'net_profit', f.net_profit,
            'total_equity', f.total_equity,
            'total_assets', f.total_assets
        ) ORDER BY f.financial_year DESC)
        FROM financial_statements f
        WHERE f.company_id = c.organization_number
    ) as financials,
    (
        SELECT jsonb_agg(jsonb_build_object(
            'role_description', COALESCE(rt.description, 'Ukjent rolle'),
            'person_name', COALESCE(
                NULLIF(TRIM(CONCAT_WS(' ', p.first_name, p.middle_name, p.last_name)), ''), 
                hc.name
            )
        ))
        FROM company_roles cr
        LEFT JOIN role_types rt ON cr.role_type_code = rt.code
        LEFT JOIN people p ON cr.person_id = p.id
        LEFT JOIN companies hc ON cr.holding_company_id = hc.organization_number
        WHERE cr.company_id = c.organization_number AND cr.is_active = true
    ) as roles,
    (
        SELECT jsonb_agg(jsonb_build_object(
            'organization_number', loc.organization_number,
            'name', loc.name,
            'city', loc.city,
            'postal_code', loc.postal_code,
            'employee_count', loc.employee_count
        ))
        FROM company_locations loc
        WHERE loc.company_id = c.organization_number
    ) as locations
FROM companies c
LEFT JOIN organization_types ot ON c.organization_type_code = ot.code
WHERE c.organization_number = %s;
"""

with connection.cursor() as cursor:
    cursor.execute(sql, [org_number])
    rows = cursor.fetchall()
    print("QUERY PLAN:")
    for r in rows:
        print(r[0])
