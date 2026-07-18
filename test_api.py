import os
import django
import sys
import json
from datetime import date

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from myapi.company_controller import CompanyController
from myapi.models import Company

# Custom JSON encoder to handle dates
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()
        return super(DateTimeEncoder, self).default(obj)

print("Starting API Test...")
company = Company.objects.first()

if not company:
    print("ERROR: Database is empty. Did you run import_data.py?")
else:
    print(f"Found Company: {company.name} ({company.organization_number})")
    print("Passing to CompanyController...")
    
    controller = CompanyController()
    try:
        response = controller.get_company(company.organization_number)
        print("\nAPI Response Generated Successfully! Here is the JSON:")
        print(json.dumps(response, indent=2, cls=DateTimeEncoder))
    except Exception as e:
        print(f"\nAPI CRASHED: {e}")
