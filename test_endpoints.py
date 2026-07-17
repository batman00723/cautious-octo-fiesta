import urllib.request
import json

BASE_URL = 'http://127.0.0.1:8000'

endpoints = [
    '/api/search/?q=data',
    '/api/ssg/routes',
    '/api/companies/983975240',
    '/api/companies/983975240/similar',
    '/api/hubs/municipalities/all',
    '/api/hubs/industries/all',
    '/api/hubs/municipality/0301',
    '/api/hubs/industry/62.010',
    '/api/sitemap/index.xml',
    '/api/sitemap/hubs.xml',
    '/api/sitemap/companies_1.xml'
]

for ep in endpoints:
    url = BASE_URL + ep
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            status = response.status
            content_type = response.headers.get('Content-Type')
            data = response.read()
            size = len(data)
            print(f"✅ [200] {ep} (Type: {content_type}, Size: {size} bytes)")
    except Exception as e:
        print(f"❌ [ERROR] {ep}: {e}")
