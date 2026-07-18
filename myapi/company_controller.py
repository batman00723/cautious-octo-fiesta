import random
from ninja_extra import api_controller, route
from django.shortcuts import get_object_or_404
from ninja import Schema
from typing import Optional, Dict, Any, List
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
    business_address: Optional[Dict[str, Any]]
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

def generate_programmatic_summary(company: Company) -> str:
    """Zero-cost AI logic that injects DB facts into randomly selected templates (Norwegian)."""
    industry_obj = company.industries.filter(is_primary=True).first()
    industry_name = industry_obj.industry.description.lower() if industry_obj else "ulike næringer"

    latest_financials = company.financials.order_by('-financial_year').first()
    revenue = f"{latest_financials.operating_revenue:,} NOK" if latest_financials and latest_financials.operating_revenue else "ukjent omsetning"
    
    name = company.name
    city = company.business_city or "Norge"
    year = company.established_date.year if company.established_date else "nylig"
    employees = company.employee_count
    org_type = company.organization_type.description.lower() if company.organization_type else "virksomhet"

    templates = [
        f"**{name}** er en aktiv {org_type} innenfor bransjen {industry_name}. Selskapet ble etablert i {year} med hovedkontor i {city}, og har i dag {employees} ansatte. I det siste årsregnskapet rapporterte de en driftsinntekt på {revenue}.",
        f"**{name}** holder til i {city} og ble opprettet i {year} som en {org_type}. De spesialiserer seg innen {industry_name} og har for tiden {employees} ansatte. Deres seneste regnskapstall viser {revenue} i driftsinntekter.",
        f"Med base i {city} er **{name}** en aktør i bransjen for {industry_name}. Selskapet er organisert som en {org_type}, ble stiftet i {year}, og har i dag {employees} ansatte. Selskapet rapporterte nylig {revenue} i driftsinntekter."
    ]

    random.seed(company.organization_number) 
    return random.choice(templates)


@api_controller('/companies', tags=['Company Details'])
class CompanyController:
    
    @route.get('/{org_number}', response=CompanyDetailSchema)
    def get_company(self, org_number: str):
        # Optimized prefetch to grab absolutely everything in one fast SQL query
        company = get_object_or_404(
            Company.objects.prefetch_related(
                'financials', 
                'roles__person', 
                'roles__holding_company', 
                'roles__role_type',
                'industries__industry',
                'locations'
            ), 
            organization_number=org_number
        )
        
        # 1. Map Industries
        inds = [{"code": i.industry.code, "description": i.industry.description, "is_primary": i.is_primary} for i in company.industries.all()]
            
        # 2. Map Financials (Sort by newest year first)
        fins = []
        for fin in sorted(company.financials.all(), key=lambda x: x.financial_year, reverse=True):
            fins.append({
                "financial_year": fin.financial_year,
                "operating_revenue": fin.operating_revenue,
                "operating_profit": fin.operating_profit,
                "net_profit": fin.net_profit,
                "total_equity": fin.total_equity,
                "total_assets": fin.total_assets
            })
            
        # 3. Map Roles (Board of Directors, CEO, etc.)
        roles = []
        for r in company.roles.filter(is_active=True):
            person_name = None
            if r.person:
                parts = filter(None, [r.person.first_name, r.person.middle_name, r.person.last_name])
                person_name = " ".join(parts)
            elif r.holding_company:
                person_name = r.holding_company.name
                
            roles.append({
                "role_description": r.role_type.description if r.role_type else "Ukjent rolle",
                "person_name": person_name
            })
            
        # 4. Map Branch Locations
        locs = []
        for loc in company.locations.all():
            locs.append({
                "organization_number": loc.organization_number,
                "name": loc.name,
                "city": loc.city,
                "postal_code": loc.postal_code,
                "employee_count": loc.employee_count
            })
        
        return {
            # Base info
            "organization_number": company.organization_number,
            "name": company.name,
            "organization_type": company.organization_type.description if company.organization_type else None,
            "established_date": str(company.established_date) if company.established_date else None,
            "registered_date": str(company.registered_date) if company.registered_date else None,
            "employee_count": company.employee_count,
            "website": company.website,
            "business_address": company.business_address,
            "business_postal_code": company.business_postal_code,
            "business_city": company.business_city,
            "business_country_code": company.business_country_code,
            "purpose": company.purpose,
            "ai_summary": generate_programmatic_summary(company),
            
            # Trust & Warnings
            "is_vat_registered": company.is_vat_registered,
            "is_bankrupt": company.is_bankrupt,
            "is_under_liquidation": company.is_under_liquidation,
            
            # Arrays
            "financials": fins,
            "roles": roles,
            "industries": inds,
            "locations": locs
        }

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
