from ninja_extra import api_controller, route
from typing import List
from ninja import Schema
from .models import Company, Municipality, Industry

class RoutesSchema(Schema):
    organization_numbers: List[str]
    municipalities: List[str]
    industries: List[str]

@api_controller('/ssg', tags=['Next.js Build Routes'])
class SSGController:
    
    @route.get('/routes', response=RoutesSchema)
    def get_ssg_routes(self):
        """
        Returns the master arrays of IDs so Next.js knows exactly which pages to bake.
        """
        orgs = list(Company.objects.values_list('organization_number', flat=True))
        munis = list(Municipality.objects.values_list('municipality_code', flat=True))
        inds = list(Industry.objects.values_list('code', flat=True))
        
        return {
            "organization_numbers": orgs,
            "municipalities": munis,
            "industries": inds
        }
