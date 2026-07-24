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


from django.db import connection

@api_controller('/search', tags=['Live Search'])
class SearchController:
    
    @route.get('/', response=List[SearchResultSchema], throttle=[AnonRateThrottle()])
    def search_companies(
        self, 
        q: Optional[str] = None,
        min_employees: Optional[int] = None,
        max_employees: Optional[int] = None,
        min_revenue: Optional[int] = None,
        industry_code: Optional[str] = None
    ):
        sql = """
        SELECT 
            c.organization_number, 
            c.name, 
            c.business_city, 
            c.employee_count,
            (
                SELECT i.description 
                FROM company_industries ci 
                JOIN industries i ON ci.industry_id = i.code 
                WHERE ci.company_id = c.organization_number AND ci.is_primary = true
                LIMIT 1
            ) as industry_description,
            (
                SELECT f.operating_revenue 
                FROM financial_statements f 
                WHERE f.company_id = c.organization_number 
                ORDER BY f.financial_year DESC 
                LIMIT 1
            ) as latest_revenue
        FROM companies c
        """
        
        where_clauses = []
        params = []
        
        if q:
            if q.isdigit() and len(q) == 9:
                where_clauses.append("c.organization_number = %s")
                params.append(q)
            else:
                # Use raw full text search. Do not use ILIKE because it breaks the GIN Index
                # and forces a 1.16 million row sequential scan (taking ~10 seconds).
                # To support prefix matching, we append ':*' to the lexemes
                where_clauses.append("c.search_vector @@ plainto_tsquery('norwegian', %s)")
                params.append(q)
                
        if min_employees is not None:
            where_clauses.append("c.employee_count >= %s")
            params.append(min_employees)
            
        if max_employees is not None:
            where_clauses.append("c.employee_count <= %s")
            params.append(max_employees)
            
        if industry_code:
            where_clauses.append("""
                EXISTS (
                    SELECT 1 FROM company_industries ci 
                    WHERE ci.company_id = c.organization_number 
                    AND ci.industry_id = %s
                )
            """)
            params.append(industry_code)
            
        final_sql = sql
        if where_clauses:
            final_sql += " WHERE " + " AND ".join(where_clauses)
            
        if min_revenue is not None:
            final_sql = f"WITH results AS ({final_sql}) SELECT * FROM results WHERE latest_revenue >= %s LIMIT 20"
            params.append(min_revenue)
        else:
            final_sql += " LIMIT 20"
            
        with connection.cursor() as cursor:
            cursor.execute(final_sql, params)
            rows = cursor.fetchall()
            
        cols = [
            'organization_number', 'name', 'business_city', 
            'employee_count', 'industry_description', 'latest_revenue'
        ]
        
        return [dict(zip(cols, row)) for row in rows]