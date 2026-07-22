import random
from ninja_extra import api_controller, route
from typing import Optional, Dict, Any, List
from ninja import Schema
from django.shortcuts import get_object_or_404
import json
from django.db import connection
from django.http import Http404
from .models import Company

class SimilarCompanySchema(Schema):
    organization_number: str
    name: str
    business_city: Optional[str]
    employee_count: int

# --- Nested Schemas for the Company Detail Page ---
class FinancialSchema(Schema):
    financial_year: int
    operating_revenue: Optional[int]
    operating_profit: Optional[int]
    net_profit: Optional[int]
    total_equity: Optional[int]
    total_assets: Optional[int]

class RoleSchema(Schema):
    role_description: str
    person_name: Optional[str]

class IndustrySchema(Schema):
    code: str
    description: str
    is_primary: bool

class LocationSchema(Schema):
    organization_number: str
    name: str
    city: Optional[str]
    postal_code: Optional[str]
    employee_count: int

class CompanyDetailSchema(Schema):
    organization_number: str
    name: str
    organization_type: Optional[str]
    established_date: Optional[str]
    registered_date: Optional[str]
    employee_count: int
    website: Optional[str]
    business_address: Optional[Any]
    business_postal_code: Optional[str]
    business_city: Optional[str]
    business_country_code: Optional[str]
    purpose: Optional[str]
    ai_summary: str
    
    # Trust & Warning Flags
    is_vat_registered: bool
    is_bankrupt: bool
    is_under_liquidation: bool
    
    # Nested Arrays
    financials: List[FinancialSchema]
    roles: List[RoleSchema]
    industries: List[IndustrySchema]
    locations: List[LocationSchema]

def generate_programmatic_summary(data: dict) -> str:
    """Zero-cost AI logic that injects DB facts into randomly selected templates (Norwegian)."""
    industry_name = "ulike næringer"
    for ind in (data.get('industries') or []):
        if ind.get('is_primary'):
            industry_name = ind.get('description', '').lower()
            break

    revenue = "ukjent omsetning"
    fins = data.get('financials') or []
    if fins and fins[0].get('operating_revenue') is not None:
        revenue = f"{fins[0]['operating_revenue']:,} NOK"
    
    name = data.get('name', '')
    city = data.get('business_city') or "Norge"
    est_date = data.get('established_date')
    year = est_date[:4] if est_date else "nylig"
    employees = data.get('employee_count', 0)
    org_type = (data.get('organization_type') or "virksomhet").lower()

    templates = [
        f"**{name}** er en aktiv {org_type} innenfor bransjen {industry_name}. Selskapet ble etablert i {year} med hovedkontor i {city}, og har i dag {employees} ansatte. I det siste årsregnskapet rapporterte de en driftsinntekt på {revenue}.",
        f"**{name}** holder til i {city} og ble opprettet i {year} som en {org_type}. De spesialiserer seg innen {industry_name} og har for tiden {employees} ansatte. Deres seneste regnskapstall viser {revenue} i driftsinntekter.",
        f"Med base i {city} er **{name}** en aktør i bransjen for {industry_name}. Selskapet er organisert som en {org_type}, ble stiftet i {year}, og har i dag {employees} ansatte. Selskapet rapporterte nylig {revenue} i driftsinntekter."
    ]

    random.seed(data.get('organization_number')) 
    return random.choice(templates)


@api_controller('/companies', tags=['Company Details'])
class CompanyController:
    
    @route.get('/{org_number}', response=CompanyDetailSchema)
    def get_company(self, org_number: str):
        # OPTION B: ONE SINGLE QUERY FOR MAXIMUM SPEED
        sql = """
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
            row = cursor.fetchone()
            
        if not row:
            raise Http404("Company not found")
            
        # Map row tuple to dictionary keys based on SELECT order
        cols = [
            'organization_number', 'name', 'organization_type', 'established_date', 
            'registered_date', 'employee_count', 'website', 'business_address', 
            'business_postal_code', 'business_city', 'business_country_code', 'purpose', 
            'is_vat_registered', 'is_bankrupt', 'is_under_liquidation', 
            'industries', 'financials', 'roles', 'locations'
        ]
        data = dict(zip(cols, row))
        
        # Parse JSON arrays (Postgres might return them as strings depending on psycopg2 version)
        for key in ['industries', 'financials', 'roles', 'locations']:
            val = data.get(key)
            if isinstance(val, str):
                data[key] = json.loads(val)
            else:
                data[key] = val or []
        
        # Format dates to string
        if data['established_date']: data['established_date'] = str(data['established_date'])
        if data['registered_date']: data['registered_date'] = str(data['registered_date'])
        
        data['ai_summary'] = generate_programmatic_summary(data)
        
        return data

    @route.get('/{org_number}/similar', response=List[SimilarCompanySchema])
    def get_similar_companies(self, org_number: str):
        company = get_object_or_404(Company, organization_number=org_number)
        
        qs = Company.objects.exclude(organization_number=org_number)
        primary_ind = company.industries.filter(is_primary=True).first()
        
        if company.business_city:
            qs = qs.filter(business_city__iexact=company.business_city)
            
        if primary_ind:
            qs = qs.filter(industries__industry=primary_ind.industry)
            
        similar = list(qs.order_by('-employee_count')[:5])
        
        if len(similar) < 5 and primary_ind:
            fallback_qs = Company.objects.exclude(organization_number=org_number).filter(
                industries__industry=primary_ind.industry
            ).order_by('-employee_count')[:5]
            
            existing_ids = {c.organization_number for c in similar}
            for peer in fallback_qs:
                if peer.organization_number not in existing_ids:
                    similar.append(peer)
                if len(similar) >= 5:
                    break
                    
        return similar
