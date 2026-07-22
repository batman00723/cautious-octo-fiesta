# ASData - Norwegian Business Intelligence Engine

ASData is a high-performance business intelligence platform and data pipeline that aggregates, processes, and serves data for all 1.16 million registered companies in Norway. It provides instant access to official registry data, board member networks, and historical financial statements.

## 🏗 Architecture Overview

The system is split into two primary domains:

1. **The Data Engineering Pipeline:** A set of highly concurrent Python scripts using `aiohttp` and `asyncio` to extract data from the Brreg (Brønnøysund Register Centre) API. It handles rate limiting, network failures, and auto-resumes for massive datasets.
2. **The Django Backend API:** A Django REST backend using **Django Ninja Extra** (Class-Based Controllers) connected to a **Supabase (PostgreSQL)** database. It uses advanced GIN Indexes for sub-millisecond full-text search and complex Subqueries for historical financial filtering.

---

## 🚀 The Data Pipeline (`Production_Pipeline`)

If you need to update the data or re-scrape the 1.16 million companies, navigate to the data engineering folder and run the scripts sequentially.

### 1. Data Extraction
* `1_fetch_all_companies.py`: Downloads the master list of all Norwegian companies (including ENK, AS, etc.) and their basic metadata.
* `2_fetch_all_financials.py`: Iterates through companies to download up to 5 years of historical financial statements. Only applicable to company types required to report financials (e.g., AS).
* `3_fetch_all_roles.py`: Extracts the Board of Directors, CEOs, and corporate ownership webs for every company. It maps unique individuals to track "who knows who" across the Norwegian economy.
* `4_transform_companies.py`: Cleans and formats the raw JSON company data into a structured CSV format.
* `5_generate_dictionaries.py`: Extracts the unique lookup tables (Industries, Municipalities, Organization Types) to build the relational database schema.

*Note: The scrapers use `NO_DATA` marker rows to track progress and prevent infinite retries on companies that legally have no data to report.*

### 2. Database Ingestion (`import_data.py`)
To push the massive generated `.csv` files into Supabase, use the `import_data.py` script located in the Django root.

```bash
python import_data.py
```
**Safety Mechanisms in `import_data.py`:**
* **Duplicate Prevention:** It checks `COUNT(*)` on each table. If a table has data, it skips the import for that table.
* **Orphan Cleanup:** It actively filters out empty `NO_DATA` marker rows and invalid government Foreign Keys (e.g., industry code `38.310`) to prevent PostgreSQL constraint crashes.
* **Chunking:** It uses Pandas `to_sql` with `chunksize=500` to prevent Supabase connection timeouts.

---

## 💻 The Backend API (`myapi`)

The backend is built using Django and Ninja Extra. All business logic is encapsulated in controllers located in `myapi/`.

### Key Endpoints
* `GET /api/search/`: The **"Super Search"** endpoint. It uses PostgreSQL GIN Full-Text Search on the `search_vector` column. It also supports dynamic filtering:
  * `min_employees` / `max_employees`
  * `industry_code`
  * `min_revenue` (Uses an advanced SQL Subquery to dynamically evaluate against the company's absolute most recent financial year, bypassing outdated historical rows).
* `GET /api/companies/{org_number}`: The highly optimized detail page. It uses `prefetch_related` to grab the company, all financial years, all board roles, and all industries in a single lightning-fast SQL query.

### Database Schema Highlights
* `companies`: The core table. `organization_number` is the Primary Key.
* `financial_statements`: 1-to-Many relationship with `companies`. Contains historical revenue, profit, and equity.
* `company_roles`: The junction table mapping `companies` to `people` (or holding companies). `person_id` and `holding_company_id` are nullable.
* `company_industries`: 1-to-Many relationship mapping companies to their respective industry codes.

---

## 🛠 Local Setup for Maintainers

**1. Clone and configure environment:**
```bash
git clone <repository_url>
cd mvp_asdata
python -m venv venv
.\venv\Scripts\activate  # (Windows)
pip install -r requirements.txt
```

**2. Setup Supabase `.env`:**
Create a `.env` file in the root directory:
```env
SECRET_KEY=your_django_secret
DEBUG=True
DB_NAME=postgres
DB_USER=postgres.[project_id]
DB_PASSWORD=your_password
DB_HOST=aws-0-[region].pooler.supabase.com
DB_PORT=5432
DB_URL=postgresql://[user]:[password]@[host]:5432/postgres
```

**3. Initialize Database:**
If starting fresh or pointing to a new Supabase project:
```bash
python manage.py makemigrations
python manage.py migrate
python import_data.py  # Only if you need to ingest the 1.16M rows
```

**4. Run the Server:**
```bash
python manage.py runserver
```
Navigate to `http://127.0.0.1:8000/api/docs` to view the auto-generated Swagger documentation.
