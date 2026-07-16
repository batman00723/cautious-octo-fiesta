from ninja_extra import api_controller, route
from ninja import Schema
from typing import List, Optional
from .models import Company

class SearchResultSchema(Schema):
    organization_number: str
    name: str
    business_city: Optional[str]
    industry_description: Optional[str]


@api_controller('/search', tags=['Live Search'])
class SearchController:
    
    @route.get('/', response=List[SearchResultSchema])
    def search_companies(self, q: str):
        if not q or len(q) < 2:
            return []
            
        # Fast direct ID search
        if q.isdigit() and len(q) == 9:
            qs = Company.objects.filter(organization_number=q)
            if qs.exists():
                company = qs.first()
                primary_ind = company.industries.filter(is_primary=True).first()
                return [{
                    "organization_number": company.organization_number,
                    "name": company.name,
                    "business_city": company.business_city,
                    "industry_description": primary_ind.industry.description if primary_ind else None
                }]
                
        # PostgreSQL GIN Full Text Search
        qs = Company.objects.filter(search_vector=q)[:20]
        
        results = []
        for company in qs:
            primary_ind = company.industries.filter(is_primary=True).first()
            ind_desc = primary_ind.industry.description if primary_ind else None
            
            results.append({
                "organization_number": company.organization_number,
                "name": company.name,
                "business_city": company.business_city,
                "industry_description": ind_desc
            })
            
        return results