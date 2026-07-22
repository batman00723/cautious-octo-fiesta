from django.db import models
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex


# 1. Dictionary / Reference Tables

class Industry(models.Model):
    code = models.CharField(max_length=10, primary_key=True)
    description = models.TextField()
    parent_code = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        db_table = 'industries'

class Municipality(models.Model):
    municipality_code = models.CharField(max_length=4, primary_key=True)
    name = models.TextField()

    class Meta:
        db_table = 'municipalities'

class OrganizationType(models.Model):
    code = models.CharField(max_length=10, primary_key=True)
    description = models.TextField()

    class Meta:
        db_table = 'organization_types'

class RoleType(models.Model):
    code = models.CharField(max_length=20, primary_key=True)
    description = models.TextField()
    group_code = models.CharField(max_length=20, null=True, blank=True)
    group_description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'role_types'


 
# 2. Core Tables
 

class Company(models.Model):
    # We MUST use organization_number as the Primary Key so the CSV Foreign Keys map correctly!
    organization_number = models.CharField(max_length=9, primary_key=True)
    name = models.TextField()
    
    organization_type = models.ForeignKey(OrganizationType, on_delete=models.SET_NULL, null=True, db_column='organization_type_code')
    
    established_date = models.DateField(null=True, blank=True)
    registered_date = models.DateField(null=True, blank=True)
    vat_registered_date = models.DateField(null=True, blank=True)
    
    employee_count = models.IntegerField(default=0)
    website = models.TextField(null=True, blank=True)
    
    # JSONB Address Fields
    business_address = models.JSONField(null=True, blank=True)
    business_postal_code = models.CharField(max_length=10, null=True, blank=True)
    business_city = models.TextField(null=True, blank=True)
    business_country_code = models.CharField(max_length=2, null=True, blank=True)
    
    postal_address = models.JSONField(null=True, blank=True)
    postal_code = models.CharField(max_length=10, null=True, blank=True)
    city = models.TextField(null=True, blank=True)
    country_code = models.CharField(max_length=2, null=True, blank=True)
    
    # Sector & Flags
    institutional_sector_code = models.CharField(max_length=20, null=True, blank=True)
    institutional_sector_name = models.TextField(null=True, blank=True)
    
    is_vat_registered = models.BooleanField(default=False)
    is_registered_business_register = models.BooleanField(default=False)
    is_registered_foundation = models.BooleanField(default=False)
    is_registered_voluntary = models.BooleanField(default=False)
    is_bankrupt = models.BooleanField(default=False)
    is_under_liquidation = models.BooleanField(default=False)
    is_under_forced_liquidation = models.BooleanField(default=False)
    
    purpose = models.TextField(null=True, blank=True)
    
    # PostgreSQL Full Text Search (Gives us Google-like search speed)
    search_vector = SearchVectorField(null=True, blank=True)

    class Meta:
        db_table = 'companies'
        indexes = [
            # GIN index on search vector for lightning-fast text searching
            GinIndex(fields=['search_vector']),
            # Index employee count & registered date for fast sorting/ranking
            models.Index(fields=['employee_count', 'registered_date']) 
        ]

class Person(models.Model):
    first_name = models.TextField(null=True, blank=True)
    middle_name = models.TextField(null=True, blank=True)
    last_name = models.TextField(null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    is_deceased = models.BooleanField(default=False)

    class Meta:
        db_table = 'people'


# 3. Relational / Junction Tables

class CompanyIndustry(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='industries')
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = 'company_industries'
        unique_together = ('company', 'industry')

class CompanyLocation(models.Model):
    organization_number = models.CharField(max_length=9, unique=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='locations')
    organization_type = models.ForeignKey(OrganizationType, on_delete=models.SET_NULL, null=True, db_column='organization_type_code')
    
    name = models.TextField()
    website = models.TextField(null=True, blank=True)
    employee_count = models.IntegerField(default=0)
    
    business_address = models.JSONField(null=True, blank=True)
    postal_code = models.CharField(max_length=10, null=True, blank=True)
    city = models.TextField(null=True, blank=True)
    country_code = models.CharField(max_length=2, null=True, blank=True)
    postal_address = models.JSONField(null=True, blank=True)
    
    registered_date = models.DateField(null=True, blank=True)
    established_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'company_locations'

class FinancialStatement(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='financials')
    journal_number = models.CharField(max_length=50, null=True, blank=True)
    financial_year = models.IntegerField()
    
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    
    currency = models.CharField(max_length=3, default='NOK')
    accounting_type = models.CharField(max_length=10, null=True, blank=True)
    statement_plan = models.CharField(max_length=50, null=True, blank=True)
    
    is_liquidation_statement = models.BooleanField(default=False)
    is_small_business = models.BooleanField(default=False)
    accounting_rules = models.CharField(max_length=50, null=True, blank=True)
    audit_exempt = models.BooleanField(default=False)
    
    # Financial metrics (Using BigIntegerField because Revenue in NOK can easily exceed 2 billion integer limit)
    total_assets = models.BigIntegerField(null=True, blank=True)
    total_equity = models.BigIntegerField(null=True, blank=True)
    operating_revenue = models.BigIntegerField(null=True, blank=True)
    operating_profit = models.BigIntegerField(null=True, blank=True)
    net_profit = models.BigIntegerField(null=True, blank=True)
    
    raw_json = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'financial_statements'
        unique_together = ('company', 'financial_year')
        indexes = [
            models.Index(fields=['financial_year', 'operating_revenue']),
        ]

class CompanyRole(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='roles')
    # Can be a Human Person
    person = models.ForeignKey(Person, on_delete=models.CASCADE, null=True, blank=True)
    # Or can be an Entity (like a Corporate Auditing firm)
    holding_company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name='corporate_roles')
    
    role_type = models.ForeignKey(RoleType, on_delete=models.CASCADE, db_column='role_type_code')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'company_roles'



class DeletionRequest(models.Model):                                                                                                                                               
    organization_number = models.CharField(max_length=9)                                                                                                                           
    name = models.CharField(max_length=255)                                                                                                                                        
    email = models.EmailField()                                                                                                                                                    
    reason = models.TextField(null=True, blank=True)                                                                                                                               
    created_at = models.DateTimeField(auto_now_add=True)  


    class Meta:                                                                                                                                                                    
        db_table = 'deletion_requests' 


class ContactMessage(models.Model):                                                                                                                                                                                                                                                                                                                                                         
                                                                                                                                                                                                      
    name = models.CharField(max_length=255)                                                                                                                                                       
    email = models.EmailField()                                                                                                                                                                   
    phone_number = models.CharField(max_length=20, null=True, blank=True)                                                                                                                         
    message = models.TextField()                                                                                                                                                                  
                                                                                                                                                                                                                                                                                                                 
    created_at = models.DateTimeField(auto_now_add=True)                                                                                                                                          
                                                                                                                                                                                                      
    class Meta:                                                                                                                                                                                   
        db_table = 'contact_messages'                                                                                                                                                             
        ordering = ['-created_at']                                                                                                                                                                
                                                                                                                                                                                                      
    def __str__(self):                                                                                                                                                                            
        return f"Message from {self.name})"                                                                                                                                        
