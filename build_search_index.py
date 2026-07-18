import os
import django
import sys

# Setup Django Environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.postgres.search import SearchVector
from myapi.models import Company

print("🚀 Building PostgreSQL Full-Text Search Index...")

# We combine the company name (Weight A - Highest priority) 
# and the city (Weight B - Secondary priority) into the vector.
# This allows a user to type "TechCorp Oslo" and find it instantly.
Company.objects.update(
    search_vector=SearchVector('name', weight='A', config='norwegian') + SearchVector('business_city', weight='B', config='norwegian')
)

print("✅ Search Index Built Successfully! The Live Search API is now fully activated.")
