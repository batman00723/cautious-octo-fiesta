import time
import urllib.request
import json

def test_endpoint(name, url):
    print(f"\n==========================================")
    print(f"[TEST] Testing: {name}")
    print(f"GET {url}")
    
    try:
        start = time.perf_counter()
        req = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                elapsed = time.perf_counter() - start
                status_code = response.getcode()
                body = response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            elapsed = time.perf_counter() - start
            status_code = e.code
            body = e.read().decode('utf-8')
            
        print(f"Time: {elapsed*1000:.1f}ms")
        print(f"Status Code: {status_code}")
        
        if status_code == 200:
            try:
                data = json.loads(body)
                if isinstance(data, list):
                    print(f"[SUCCESS] Returned: List of {len(data)} items")
                    if len(data) > 0:
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
            print("[ERROR] Error Response:", body)
            
    except Exception as e:
        print("[FATAL] Request failed:", e)

# Give the server a couple seconds to fully bind to the port
print("Waiting 5 seconds for Django runserver to boot up...")
time.sleep(5)

base_url = "http://127.0.0.1:8000"
sample_org = "810034882"

test_endpoint("Company Detail (Fast Raw SQL)", f"{base_url}/api/companies/{sample_org}")
test_endpoint("Similar Companies API", f"{base_url}/api/companies/{sample_org}/similar")
test_endpoint("Super Search - Exact Org Number", f"{base_url}/api/search/?q={sample_org}")
test_endpoint("Super Search - Text + Revenue > 1B NOK", f"{base_url}/api/search/?q=Equinor&min_revenue=1000000000")
test_endpoint("Super Search - Employees (50 to 100)", f"{base_url}/api/search/?min_employees=50&max_employees=100")
