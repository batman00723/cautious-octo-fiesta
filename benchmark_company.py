import time
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from myapi.models import Company
from myapi.company_controller import CompanyController

# Pick a real org number from the DB
sample_org = Company.objects.first().organization_number
print(f"Testing with org number: {sample_org}")

# Simulate what the API does - run 5 times to get an average
times = []
controller = CompanyController()
for i in range(5):
    start = time.perf_counter()
    data = controller.get_company(sample_org)
    elapsed = time.perf_counter() - start
    times.append(elapsed)
    print(f"  Run {i+1}: {elapsed*1000:.1f}ms")

avg = sum(times) / len(times)
print(f"\nAverage: {avg*1000:.1f}ms")
print(f"Min:     {min(times)*1000:.1f}ms")
print(f"Max:     {max(times)*1000:.1f}ms")
