import os
import sys
import django
from django.db import connection
from django.contrib.postgres.search import SearchQuery
from django.db.models import Subquery, OuterRef, BigIntegerField

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from myapi.models import Company, FinancialStatement

def test_search():
    q = "Equinor"
    min_revenue = 1000000000
    
    qs = Company.objects.all()
    vector_qs = qs.filter(search_vector=SearchQuery(q, config='norwegian'))
    qs = vector_qs
    
    latest_revenue_sq = FinancialStatement.objects.filter(
        company_id=OuterRef('organization_number')
    ).order_by('-financial_year').values('operating_revenue')[:1]
    
    qs = qs.annotate(
        latest_revenue=Subquery(latest_revenue_sq, output_field=BigIntegerField())
    )
    
    qs = qs.filter(latest_revenue__gte=min_revenue)[:20]
    
    print("Executing EXPLAIN ANALYZE for the Search API query...")
    with connection.cursor() as cursor:
        cursor.execute("EXPLAIN ANALYZE " + str(qs.query))
        for row in cursor.fetchall():
            print(row[0])

if __name__ == '__main__':
    test_search()
