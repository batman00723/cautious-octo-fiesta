from ninja_extra import api_controller, route
from ninja_extra.throttling import AnonRateThrottle
from ninja import Schema
from typing import List, Optional
from django.contrib.postgres.search import SearchQuery
from django.db.models import Subquery, OuterRef, BigIntegerField
from .models import Company, FinancialStatement

class SearchResultSchema(Schema):
    organization_number: str
    name: str
    business_city: Optional[str]
    industry_description: Optional[str]
    employee_count: Optional[int]
    latest_revenue: Optional[int] = None


@api_controller('/search', tags=['Live Search'])
class SearchController:
    
    @route.get('/', response=List[SearchResultSchema], throttle=[AnonRateThrottle()])
    async def search_companies(
        self, 
        q: Optional[str] = None,
        min_employees: Optional[int] = None,
        max_employees: Optional[int] = None,
        min_revenue: Optional[int] = None,
        industry_code: Optional[str] = None
    ):
        qs = Company.objects.all()

        # 1. Text Search
        if q:
            # Fast direct ID search
            if q.isdigit() and len(q) == 9:
                qs = qs.filter(organization_number=q)
            else:
                # PostgreSQL GIN Full Text Search
                vector_qs = qs.filter(search_vector=SearchQuery(q, config='norwegian'))
                if await vector_qs.aexists():
                    qs = vector_qs
                else:
                    qs = qs.filter(name__icontains=q)
        
        # 2. Employee Filters
        if min_employees is not None:
            qs = qs.filter(employee_count__gte=min_employees)
        if max_employees is not None:
            qs = qs.filter(employee_count__lte=max_employees)
            
        # 3. Industry Filter
        if industry_code:
            qs = qs.filter(industries__industry__code=industry_code)
            
        # 4. Revenue Filter (Dynamic Latest Year using Subquery)
        # We annotate every company with its most recent operating_revenue
        latest_revenue_sq = FinancialStatement.objects.filter(
            company_id=OuterRef('organization_number')
        ).order_by('-financial_year').values('operating_revenue')[:1]
        
        qs = qs.annotate(
            latest_revenue=Subquery(latest_revenue_sq, output_field=BigIntegerField())
        )
        
        if min_revenue is not None:
            qs = qs.filter(latest_revenue__gte=min_revenue)
            
        # Limit to top 20 for fast response
        qs = qs.prefetch_related('industries__industry')[:20]
        
        results = []
        async for company in qs:
            inds = [i for i in company.industries.all() if i.is_primary]
            ind_desc = inds[0].industry.description if inds else None
            
            results.append({
                "organization_number": company.organization_number,
                "name": company.name,
                "business_city": company.business_city,
                "industry_description": ind_desc,
                "employee_count": company.employee_count,
                "latest_revenue": getattr(company, 'latest_revenue', None)
            })
            
        return results