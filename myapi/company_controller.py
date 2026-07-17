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

class CompanyDetailSchema(Schema):
    organization_number: str
    name: str
    organization_type: Optional[str]
    established_date: Optional[str]
    employee_count: int
    website: Optional[str]
    business_address: Optional[List[str]]
    business_postal_code: Optional[str]
    business_city: Optional[str]
    business_country_code: Optional[str]
    purpose: Optional[str]
    ai_summary: str

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

    # Guarantees the same template is picked for the same company every time
    random.seed(company.organization_number) 
    return random.choice(templates)

@api_controller('/companies', tags=['Company Details'])
class CompanyController:
    
    @route.get('/{org_number}', response=CompanyDetailSchema)
    def get_company(self, org_number: str):
        company = get_object_or_404(Company, organization_number=org_number)
        
        return {
            "organization_number": company.organization_number,
            "name": company.name,
            "organization_type": company.organization_type.description if company.organization_type else None,
            "established_date": str(company.established_date) if company.established_date else None,
            "employee_count": company.employee_count,
            "website": company.website,
            "business_address": company.business_address,
            "business_postal_code": company.business_postal_code,
            "business_city": company.business_city,
            "business_country_code": company.business_country_code,
            "purpose": company.purpose,
            "ai_summary": generate_programmatic_summary(company)
        }

    @route.get('/{org_number}/similar', response=List[SimilarCompanySchema])
    def get_similar_companies(self, org_number: str):
        company = get_object_or_404(Company, organization_number=org_number)
        
        # Step 1: Base Query (Exclude the current company so it doesn't recommend itself)
        qs = Company.objects.exclude(organization_number=org_number)
        
        # Step 2: Try to find peers in the Exact Same City AND Same Primary Industry
        primary_ind = company.industries.filter(is_primary=True).first()
        
        if company.business_city:
            qs = qs.filter(business_city__iexact=company.business_city)
            
        if primary_ind:
            qs = qs.filter(industries__industry=primary_ind.industry)
            
        # Grab the 5 biggest peers by employee count
        similar = list(qs.order_by('-employee_count')[:5])
        
        # Step 3: Fallback. If they are in a tiny town and we didn't find 5 peers, 
        # let's just find 5 companies in the same industry from ANY city to fill the list.
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
