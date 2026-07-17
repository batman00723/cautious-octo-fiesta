from ninja_extra import api_controller, route
from ninja_extra.throttling import AnonRateThrottle
from ninja import Schema
from typing import List, Optional
from django.contrib.postgres.search import SearchQuery
from .models import Company

class SearchResultSchema(Schema):
    organization_number: str
    name: str
    business_city: Optional[str]
    industry_description: Optional[str]


@api_controller('/search', tags=['Live Search'])
class SearchController:
    
    @route.get('/', response=List[SearchResultSchema], throttle=[AnonRateThrottle()])
    async def search_companies(self, q: str):
        if not q or len(q) < 2:
            return []
            
        # Fast direct ID search
        if q.isdigit() and len(q) == 9:
            qs = Company.objects.filter(organization_number=q)
            if await qs.aexists():
                company = await qs.afirst()
                primary_ind = await company.industries.select_related('industry').filter(is_primary=True).afirst()
                return [{
                    "organization_number": company.organization_number,
                    "name": company.name,
                    "business_city": company.business_city,
                    "industry_description": primary_ind.industry.description if primary_ind else None
                }]
                
        # PostgreSQL GIN Full Text Search
        qs = Company.objects.filter(search_vector=SearchQuery(q, config='norwegian'))
        if not await qs.aexists():
            qs = Company.objects.filter(name__icontains=q)
            
        qs = qs.prefetch_related('industries__industry')[:20]
        
        results = []
        async for company in qs:
            inds = [i for i in company.industries.all() if i.is_primary]
            ind_desc = inds[0].industry.description if inds else None
            
            results.append({
                "organization_number": company.organization_number,
                "name": company.name,
                "business_city": company.business_city,
                "industry_description": ind_desc
            })
            
        return results