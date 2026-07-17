from ninja_extra import api_controller, route
from django.http import HttpResponse
from .models import Company, Municipality, Industry
import math

# The future URL of your Next.js Frontend (can be changed later)
FRONTEND_URL = "https://pexus.no"

# Google's absolute limit is 50,000. We use 45,000 to be perfectly safe.
URLS_PER_SITEMAP = 45000  

@api_controller('/sitemap', tags=['SEO Sitemaps'])
class SitemapController:
    
    @route.get('/index.xml')
    def sitemap_index(self):
        """Returns the Master Sitemap Index pointing to all sub-sitemaps"""
        total_companies = Company.objects.count()
        # If DB is empty during testing, pretend there's 1 page
        num_company_pages = max(1, math.ceil(total_companies / URLS_PER_SITEMAP))
        
        xml = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml.append('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
        
        # Add Hubs Sitemap
        xml.append(f'  <sitemap><loc>{FRONTEND_URL}/sitemap_hubs.xml</loc></sitemap>')
        
        # Add Company Sitemaps (Dynamically scales based on total companies!)
        for i in range(1, num_company_pages + 1):
            xml.append(f'  <sitemap><loc>{FRONTEND_URL}/sitemap_companies_{i}.xml</loc></sitemap>')
            
        xml.append('</sitemapindex>')
        
        return HttpResponse("\n".join(xml), content_type="application/xml")

    @route.get('/hubs.xml')
    def hubs_sitemap(self):
        """Returns the sitemap for all Hub and Spoke pages"""
        xml = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
        
        # Master Directories
        xml.append(f'  <url><loc>{FRONTEND_URL}/municipalities</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>')
        xml.append(f'  <url><loc>{FRONTEND_URL}/industries</loc><changefreq>weekly</changefreq><priority>0.9</priority></url>')
        
        # Municipalities Spoke Pages
        for muni in Municipality.objects.values_list('municipality_code', flat=True):
            xml.append(f'  <url><loc>{FRONTEND_URL}/municipalities/{muni.lower()}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>')
            
        # Industries Spoke Pages
        for ind in Industry.objects.values_list('code', flat=True):
            xml.append(f'  <url><loc>{FRONTEND_URL}/industries/{ind.lower()}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>')
            
        xml.append('</urlset>')
        return HttpResponse("\n".join(xml), content_type="application/xml")

    @route.get('/companies_{page}.xml')
    def companies_sitemap(self, page: int):
        """Returns a specific chunk of 45,000 companies based on the page number"""
        if page < 1:
            page = 1
            
        offset = (page - 1) * URLS_PER_SITEMAP
        
        # We only need the organization_number string, so values_list uses virtually zero RAM
        org_numbers = Company.objects.values_list('organization_number', flat=True)[offset:offset + URLS_PER_SITEMAP]
        
        xml = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
        
        for org in org_numbers:
            xml.append(f'  <url><loc>{FRONTEND_URL}/company/{org}</loc><changefreq>monthly</changefreq><priority>0.7</priority></url>')
            
        xml.append('</urlset>')
        return HttpResponse("\n".join(xml), content_type="application/xml")
