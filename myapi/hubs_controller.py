from ninja_extra import api_controller, route
from ninja import Schema
from typing import List, Optional
from .models import Company

class HubCompanySchema(Schema):
    organization_number: str
    name: str
    business_city: Optional[str]
    employee_count: int

@api_controller('/hubs', tags=['Hub Pages'])
class HubsController:
    
    @route.get('/municipality/{code}', response=List[HubCompanySchema])
    def get_municipality_hub(self, code: str):
        # Fetch Top 100 biggest companies in the city/municipality
        qs = Company.objects.filter(locations__city__iexact=code).order_by('-employee_count')[:100]
        return list(qs)

    @route.get('/industry/{code}', response=List[HubCompanySchema])
    def get_industry_hub(self, code: str):
        # Fetch Top 100 biggest companies in this specific NACE sector
        qs = Company.objects.filter(industries__industry__code=code).order_by('-employee_count')[:100]
        return list(qs)
