import os
import sys
import django
import time
from django.test import Client

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

client = Client()

def test_endpoint(name, url):
    print(f"\n==========================================")
    print(f"[TEST] Testing: {name}")
    print(f"GET {url}")
    
    start = time.perf_counter()
    response = client.get(url)
    elapsed = time.perf_counter() - start
    
    print(f"Time: {elapsed*1000:.1f}ms")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            if isinstance(data, list):
                print(f"[SUCCESS] Returned: List of {len(data)} items")
                if len(data) > 0:
                    # Print first item snippet
                    first = data[0]
                    name_val = first.get('name', 'Unknown')
                    print(f"First Result: {name_val}")
            elif isinstance(data, dict):
                print(f"[SUCCESS] Returned: JSON Object (Keys: {len(data.keys())})")
                print(f"Name: {data.get('name')}")
                print(f"Financial Years: {len(data.get('financials', []))}")
                print(f"Board/Roles: {len(data.get('roles', []))}")
        except Exception as e:
            print("[FAIL] Failed to parse JSON response:", e)
    else:
        print("[ERROR] Error Response:", response.content.decode('utf-8'))

# Assuming 810034882 is a valid company in the DB (usually Equinor)
sample_org = "810034882"

# 1. Test Company Detail
test_endpoint("Company Detail (Fast Raw SQL)", f"/api/companies/{sample_org}")

# 2. Test Similar Companies
test_endpoint("Similar Companies API", f"/api/companies/{sample_org}/similar")

# 3. Test Super Search - Exact Org Number
test_endpoint("Super Search - Exact Org Number", f"/api/search/?q={sample_org}")

# 4. Test Super Search - Text + Revenue Filter
test_endpoint("Super Search - Text + Revenue > 1B NOK", "/api/search/?q=Equinor&min_revenue=1000000000")

# 5. Test Super Search - Employee Filters
test_endpoint("Super Search - Employees (50 to 100)", "/api/search/?min_employees=50&max_employees=100")
