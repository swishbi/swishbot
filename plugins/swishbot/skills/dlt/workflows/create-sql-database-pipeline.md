# Create SQL Database Pipeline

Build a dlt pipeline that loads data from a SQL database into a warehouse.

**Reference example:** `examples/sql_database_pipeline.py`

## Step 1: Choose Your Approach

```
How do you access the data?
├── Direct database connection (PostgreSQL, MySQL, MSSQL, Oracle, SQLite)
│   └── Use dlt's sql_database verified source (Pattern 1)
└── SQL/query endpoint over REST API (NetSuite SuiteQL, QuickBooks Query)
    └── Build a custom source with SQL file management (Pattern 2)
```

## Pattern 1: Direct Database Connection

### Step 2a: Set Up Connection

Install the dlt extras for your database:

```bash
pip install "dlt[sql_database]"    # Core SQL support
pip install "dlt[postgres]"         # PostgreSQL
pip install "dlt[mssql]"            # SQL Server
pip install "dlt[mysql]"            # MySQL
```

### Credential Setup

dlt resolves credentials from multiple sources in priority order: **environment variables > `secrets.toml` > vault providers > default arguments**. We prefer environment variables managed through a `.env` file.

Reference: https://dlthub.com/docs/general-usage/credentials/setup

Environment variable names use uppercase with double underscores (`__`) as section separators. Define them in a `.env` file at the project root:

```bash
# .env — loaded by your orchestrator, dotenv, or shell
# IMPORTANT: .env must be in .gitignore — never commit it

# Source database credentials (for my_pipeline.py with source function arguments)
SOURCES__MY_PIPELINE__CREDENTIALS__HOST="host"
SOURCES__MY_PIPELINE__CREDENTIALS__DATABASE="database"
SOURCES__MY_PIPELINE__CREDENTIALS__USER="user"
SOURCES__MY_PIPELINE__CREDENTIALS__PASSWORD="secret"

# Destination credentials
DESTINATION__POSTGRES__CREDENTIALS__HOST="localhost"
DESTINATION__POSTGRES__CREDENTIALS__DATABASE="analytics"
DESTINATION__POSTGRES__CREDENTIALS__USER="loader"
DESTINATION__POSTGRES__CREDENTIALS__PASSWORD="secret"
```

**Note:** The section after `SOURCES__` must match the **Python module name** (the `.py` filename), not the source function name. See the [dlt credentials docs](https://dlthub.com/docs/general-usage/credentials/setup) for full naming rules.

Ensure `.env` is in `.gitignore`. Your orchestrator (Dagster, Airflow, etc.) or a `python-dotenv` call loads these at runtime.

In code, reference credentials with `dlt.secrets.value` (sensitive) or `dlt.config.value` (non-sensitive) as function parameter defaults. dlt resolves them automatically from environment variables:

```python
@dlt.source
def my_source(credentials: str = dlt.secrets.value):
    ...
```

Never hardcode credentials in pipeline code — use `dlt.secrets.value` or environment variables instead.

### Step 3a: Configure Table Selection

```python
from dlt.sources.sql_database import sql_database

source = sql_database(
    credentials=os.getenv("SOURCE_DB_CONNECTION_STRING"),
    schema="public",                              # Schema to read from
    table_names=["customers", "orders"],           # Specific tables (None = all)
    # backend="pyarrow",                           # Faster for large tables
    # backend="connectorx",                        # Fastest (requires connectorx)
)
```

### Step 4a: Configure Incremental Loading

Apply incremental hints per table to avoid full reloads:

```python
# Track changes via updated_at column
source.orders.apply_hints(
    incremental=dlt.sources.incremental("updated_at"),
    write_disposition="merge",
    primary_key="order_id",
)

# Full replace for reference/lookup tables
source.products.apply_hints(
    write_disposition="replace",
)
```

### Step 5a: Column Type Hints

Override types for columns that the source DB types ambiguously:

```python
source.orders.apply_hints(
    columns={
        "total_amount": {"data_type": "double", "nullable": True},
        "discount": {"data_type": "double", "nullable": True},
        "order_date": {"data_type": "date", "nullable": True},
    }
)
```

## Pattern 2: SQL-over-REST

Use this when the data source exposes a SQL or query endpoint over HTTP rather than a direct database connection (e.g. NetSuite SuiteQL, QuickBooks Query API).

### Step 2b: Configure Authentication

SQL-over-REST APIs typically use OAuth:

| API | Auth Method |
|-----|------------|
| NetSuite SuiteQL | OAuth1 Token-Based Authentication (TBA) |
| QuickBooks Online | OAuth2 Authorization Code with refresh token rotation |
| Custom query APIs | Bearer token, API key, or OAuth2 |

For OAuth1 (NetSuite pattern), implement a custom auth class:

```python
from requests_oauthlib import OAuth1

class OAuth1Auth:
    def __init__(self, consumer_key, consumer_secret, token, token_secret, realm):
        self.oauth = OAuth1(
            client_key=consumer_key, client_secret=consumer_secret,
            resource_owner_key=token, resource_owner_secret=token_secret,
            realm=realm, signature_method="HMAC-SHA1",
        )

    def __call__(self, request):
        request.auth = self.oauth
        return request
```

### Step 3b: Organize SQL Files

Store queries as `.sql` files in a `sql/` directory alongside the pipeline:

```
my_pipeline/
├── pipeline.py
└── sql/
    ├── customers.sql          # Active query
    ├── orders.sql
    ├── _archived_table.sql    # Prefixed with _ = skipped
    └── products.sql
```

Convention: filename (without extension) becomes the table name in the destination.

### Step 4b: Build a Custom Paginator

SQL-over-REST APIs often need custom pagination. Common pattern — wrap the query with ROWNUM/OFFSET:

```python
class RowNumPaginator(BasePaginator):
    def __init__(self, page_size=1000):
        super().__init__()
        self.page_size = page_size
        self._offset = 0

    def init_request(self, request):
        request.params["offset"] = self._offset
        request.params["limit"] = self.page_size

    def update_state(self, response, data=None):
        if not data or len(data) < self.page_size:
            self._has_next_page = False
        else:
            self._offset += self.page_size

    def update_request(self, request):
        request.params["offset"] = self._offset
        request.params["limit"] = self.page_size
```

### Step 5b: Dynamic Resource Generation

Generate one dlt resource per `.sql` file:

```python
sql_dir = Path(__file__).parent / "sql"
for sql_file in sorted(sql_dir.glob("*.sql")):
    if sql_file.stem.startswith("_"):
        continue
    query = sql_file.read_text()

    @dlt.resource(name=sql_file.stem, write_disposition="replace")
    def query_resource(_q=query):
        # POST query to API, paginate through results
        ...
        yield items
```

## Step 6: Write Dispositions

| Disposition | Use When | Example |
|-------------|----------|---------|
| `replace` | Full refresh, reference tables, small tables | `products`, `categories` |
| `merge` (delete-insert) | Transactional data with a reliable primary key | `orders`, `invoices` |
| `merge` (scd2) | Slowly-changing dimensions, need history | `employees`, `customers` |

```python
# Merge with primary key
"write_disposition": {"disposition": "merge", "strategy": "delete-insert"}
"primary_key": "order_id"

# SCD2 for change tracking
"write_disposition": {"disposition": "merge", "strategy": "scd2"}
```

## Step 7: Validate

1. **Start with one table** — get it loading correctly before adding more
2. **Check row counts** — compare source vs. destination
3. **Verify column types** — ensure numeric and date fields loaded correctly
4. **Test incremental** — run twice, confirm only delta loads on second run
5. **Check for data loss** — compare distinct keys between source and destination

```bash
python my_pipeline.py
dlt pipeline my_pipeline show
```

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*
