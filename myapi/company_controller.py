import random
from ninja_extra import api_controller, route
from django.shortcuts import get_object_or_404
from ninja import Schema
from typing import Optional, Dict, Any
from .models import Company

class CompanyDetailSchema(Schema):
    organization_number: str
    name: str
    organization_type: Optional[str]
    established_date: Optional[str]
    employee_count: int
    website: Optional[str]
    business_address: Optional[Dict[str, Any]]
    business_postal_code: Optional[str]
    business_city: Optional[str]
    business_country_code: Optional[str]
    purpose: Optional[str]
    ai_summary: str

def generate_programmatic_summary(company: Company) -> str:
    """Zero-cost AI logic that injects DB facts into randomly selected templates."""
    industry_obj = company.industries.filter(is_primary=True).first()
    industry_name = industry_obj.industry.description.lower() if industry_obj else "various business"

    latest_financials = company.financials.order_by('-financial_year').first()
    revenue = f"{latest_financials.operating_revenue:,} NOK" if latest_financials and latest_financials.operating_revenue else "undisclosed revenue"
    
    name = company.name
    city = company.business_city or "Norway"
    year = company.established_date.year if company.established_date else "recently"
    employees = company.employee_count
    org_type = company.organization_type.description if company.organization_type else "organization"

    templates = [
        f"**{name}** is an active {org_type} operating in the {industry_name} sector. Founded in {year} and headquartered in {city}, the company currently employs {employees} people. In their most recent filing, they reported {revenue}.",
        f"Located in {city}, **{name}** was established in {year} as an {org_type}. They specialize in {industry_name} and maintain a workforce of {employees} employees. Their latest financial records show {revenue}.",
        f"Operating out of {city}, **{name}** is a notable player in the {industry_name} industry. As an {org_type} founded in {year}, they have grown to {employees} employees. The company recently reported {revenue} in operating revenue."
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
