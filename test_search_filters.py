import os
import sys
import django
import asyncio
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.test import AsyncClient

async def test_search():
    client = AsyncClient()
    
    print("Test 1: Normal Search")
    res1 = await client.get('/api/search/?q=tech')
    print("Status:", res1.status_code)
    try:
        print("Data:", json.dumps(res1.json()[:2], indent=2))
    except:
        print(res1.content)
        
    print("\nTest 2: Filter by Employees (min_employees=10)")
    res2 = await client.get('/api/search/?min_employees=10')
    print("Status:", res2.status_code)
    try:
        print("Data:", json.dumps(res2.json()[:2], indent=2))
    except:
        print(res2.content)
        
    print("\nTest 3: Filter by Revenue and Employees")
    res3 = await client.get('/api/search/?min_employees=20&min_revenue=1000000')
    print("Status:", res3.status_code)
    try:
        print("Data:", json.dumps(res3.json()[:2], indent=2))
    except:
        print(res3.content)

if __name__ == "__main__":
    asyncio.run(test_search())
