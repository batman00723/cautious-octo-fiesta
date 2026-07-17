from ninja_extra import api_controller, route
from ninja import Schema
from typing import List, Optional
from .models import Company, Municipality, Industry

class HubCompanySchema(Schema):
    organization_number: str
    name: str
    business_city: Optional[str]
    employee_count: int

class MunicipalityListSchema(Schema):
    municipality_code: str
    name: str

class IndustryListSchema(Schema):
    code: str
    description: str

@api_controller('/hubs', tags=['Hub Pages'])
class HubsController:
    
    # --- MASTER DIRECTORY ENDPOINTS ---
    
    @route.get('/municipalities/all', response=List[MunicipalityListSchema])
    def get_all_municipalities(self):
        """Returns the full list of municipalities for the Master Directory page"""
        return list(Municipality.objects.order_by('name'))

    @route.get('/industries/all', response=List[IndustryListSchema])
    def get_all_industries(self):
        """Returns the full list of industries for the Master Directory page"""
        return list(Industry.objects.order_by('description'))

    # --- SPOKE PAGES (The Leaderboards) ---

    @route.get('/municipality/{code}', response=List[HubCompanySchema])
    def get_municipality_hub(self, code: str):
        """Returns the Top 100 companies in a specific city"""
        qs = Company.objects.filter(locations__city__iexact=code).order_by('-employee_count')[:100]
        return list(qs)

    @route.get('/industry/{code}', response=List[HubCompanySchema])
    def get_industry_hub(self, code: str):
        """Returns the Top 100 companies in a specific sector"""
        qs = Company.objects.filter(industries__industry__code=code).order_by('-employee_count')[:100]
        return list(qs)
