import os
import django
import sys
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from myapi.hubs_controller import HubsController

print("Testing API Controllers directly as if we were the Next.js Frontend...\n")

controller = HubsController()

print("--- 1. Testing GET /api/hubs/municipality/0301 (OSLO) ---")
try:
    muni_result = controller.get_municipality_hub("0301")
    print(f"Success! API returned {len(muni_result)} companies.")
    if len(muni_result) > 0:
        print(f"   First Company Found: {muni_result[0].name} ({muni_result[0].employee_count} ansatte)")
except Exception as e:
    print(f"❌ Crash: {e}")


print("\n--- 2. Testing GET /api/hubs/industry/84.110 ---")
try:
    # Notice we pass it in just like the URL would (it might be lowercase or exact depending on user input)
    ind_result = controller.get_industry_hub("84.110")
    print(f"Success! API returned {len(ind_result)} companies.")
    if len(ind_result) > 0:
        print(f"   First Company Found: {ind_result[0].name} ({ind_result[0].employee_count} ansatte)")
except Exception as e:
    print(f"Crash: {e}")
