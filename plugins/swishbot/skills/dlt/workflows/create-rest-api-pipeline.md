# Create REST API Pipeline

Build a dlt pipeline that loads data from a REST API into a warehouse.

**Reference example:** `examples/rest_api_pipeline.py`

## Step 1: Identify API Characteristics

Before writing code, gather these details from the API documentation:

| Characteristic | What to look for |
|---------------|-----------------|
| **Auth method** | Bearer token, API key, OAuth2, custom login endpoint |
| **Pagination style** | Link header, offset/limit, page number, cursor, none |
| **Data envelope** | Are records in `data`, `items`, `results`, or at root? |
| **Incremental field** | `modifiedDate`, `updatedAt`, `lastModified` — a sortable timestamp field |
| **Rate limits** | Requests per second/minute, concurrent request limits |

## Step 2: Configure Authentication

Choose the auth method that matches the API:

### Decision Tree

```
API requires authentication?
├── Token in header → Bearer token or API key
│   ├── "Authorization: Bearer <token>" → type: "bearer"
│   └── Custom header (X-API-Key, etc.) → type: "api_key"
├── OAuth2 → Check grant type
│   ├── client_credentials → type: "oauth2_client_credentials"
│   └── Custom flow (login endpoint, nested token) → Subclass OAuth2ClientCredentials
├── OAuth1 (e.g. NetSuite TBA) → Custom AuthBase subclass
└── HTTP Basic → type: "http_basic"
```

### Built-in Auth Types

```python
# Bearer token
"auth": {"type": "bearer", "token": dlt.secrets.value}

# API key in header
"auth": {"type": "api_key", "name": "X-API-Key", "api_key": dlt.secrets.value, "location": "header"}

# API key in query string
"auth": {"type": "api_key", "name": "apiKey", "api_key": dlt.secrets.value, "location": "query"}

# OAuth2 client credentials
"auth": {
    "type": "oauth2_client_credentials",
    "access_token_url": "https://api.example.com/oauth/token",
    "client_id": dlt.secrets.value,
    "client_secret": dlt.secrets.value,
}
```

### Custom OAuth2 (when token is in a non-standard location)

Override `build_access_token_request()` and `parse_access_token()`:

```python
from dlt.sources.helpers.rest_client.auth import OAuth2ClientCredentials

class CustomOAuth2(OAuth2ClientCredentials):
    def build_access_token_request(self):
        return {
            "url": self.access_token_url,
            "json": {"partnerId": self.client_id, "authKey": self.client_secret},
        }

    def parse_access_token(self, response):
        return response.json()["data"]["accessToken"]
```

### Credential Setup

dlt resolves credentials from multiple sources in priority order: **environment variables > `secrets.toml` > vault providers > default arguments**. We prefer environment variables managed through a `.env` file.

Reference: https://dlthub.com/docs/general-usage/credentials/setup

Environment variable names use uppercase with double underscores (`__`) as section separators. Define them in a `.env` file at the project root:

```bash
# .env — loaded by your orchestrator, dotenv, or shell
# IMPORTANT: .env must be in .gitignore — never commit it

# Source credentials (for my_pipeline.py with source function arguments)
SOURCES__MY_PIPELINE__API_TOKEN="your-token-here"
SOURCES__MY_PIPELINE__CLIENT_ID="your-client-id"
SOURCES__MY_PIPELINE__CLIENT_SECRET="your-client-secret"

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
def my_source(api_token: str = dlt.secrets.value):
    ...
```

Never hardcode credentials in pipeline code — use `dlt.secrets.value` or environment variables instead.

## Step 3: Configure Pagination

### Decision Tree

```
How does the API paginate?
├── Response has "next" link → type: "json_link" (cursor_path: "links.next")
├── Offset + limit params → type: "offset" (limit, offset_param, total_path)
├── Page number + total count → type: "page_number" or custom PageNumberTotalCountPaginator
├── Cursor/token in response → type: "cursor" or custom CursorPaginator
├── Single page (no pagination) → type: "single_page"
└── Non-standard → Subclass BasePaginator
```

### Built-in Paginators

```python
# JSON link (most common — follows "next" URL in response)
"paginator": {"type": "json_link", "next_url_path": "links.next"}

# Offset-based
"paginator": {"type": "offset", "limit": 100, "offset_param": "offset", "limit_param": "limit", "total_path": "count"}

# Page number
"paginator": {"type": "page_number", "page_param": "page", "total_path": "totalPages"}

# Single page (no pagination)
"paginator": {"type": "single_page"}
```

### Custom Paginator

Subclass `BasePaginator` and implement three methods:

```python
from dlt.sources.helpers.rest_client.paginators import BasePaginator

class MyPaginator(BasePaginator):
    def init_request(self, request):
        """Set initial pagination params on the first request."""

    def update_state(self, response, data=None):
        """Read pagination info from response; set self._has_next_page = False to stop."""

    def update_request(self, request):
        """Update request params for the next page."""
```

Register custom paginators so they can be referenced by name in config:

```python
from dlt.sources.rest_api.config_setup import register_paginator
register_paginator("my_paginator", MyPaginator)
```

## Step 4: Define Resources

Build resources **one at a time**. Get each working before adding the next.

### Simple Endpoint

```python
{
    "name": "customers",
    "endpoint": {
        "path": "customers",
        "data_selector": "items",  # JSON path to the records array
    },
}
```

### Parent-Child (Dependent) Resources

```python
# Parent
{"name": "orders", "endpoint": {"path": "orders"}, "parallelized": True},
# Child — references parent's ID
{
    "name": "order_items",
    "endpoint": {
        "path": "orders/{resources.orders.id}/items",
        "data_selector": "$",
        "paginator": {"type": "single_page"},
    },
    "include_from_parent": ["id"],
    "primary_key": ["_orders_id", "item_id"],
},
```

### Processing Steps

Add to a resource to transform records in the pipeline:

```python
"processing_steps": [
    {"map": add_metadata},                                    # Transform each record
    {"filter": lambda r: r.get("status") != "deleted"},       # Drop records
    {"yield_map": lambda r: (item for item in r["items"])},   # Flatten nested arrays
]
```

## Step 5: Configure Incremental Loading

Use incremental loading for resources that have a sortable timestamp field. This avoids full reloads on every run.

```python
"endpoint": {
    "path": "orders",
    "params": {
        "modifiedSince": "{incremental.start_value}",
        "sortBy": "modifiedDate",
    },
    "incremental": {
        "cursor_path": "modifiedDate",
        "initial_value": "2020-01-01T00:00:00Z",
        "convert": lambda dt: pendulum.parse(dt).format("YYYY-MM-DD"),
    },
}
```

### Lag for Late-Arriving Records

Some APIs have eventual consistency — records may appear after their timestamp suggests. Add `lag` (in seconds) to re-fetch a window of overlapping data:

```python
"incremental": {
    "cursor_path": "modifiedDate",
    "initial_value": "2020-01-01T00:00:00Z",
    "lag": 259200,  # 3 days in seconds
}
```

## Step 6: Set Column Types

Explicit column hints prevent dlt from inferring wrong types. Common cases:

- Numeric fields that arrive as strings (e.g. `"100.00"` → `double`)
- Date fields stored as text (e.g. `"2024-01-15"` → `timestamp`)
- Boolean fields that arrive as `"true"/"false"` strings

```python
{
    "name": "invoices",
    "columns": {
        "total_amount": {"data_type": "double", "nullable": True},
        "balance": {"data_type": "double", "nullable": True},
        "due_date": {"data_type": "timestamp", "nullable": True},
    },
}
```

### Helper Pattern

For APIs with many resources, centralize column definitions:

```python
RESOURCE_COLUMNS = {
    "invoices": {"total_amount": {"data_type": "double"}, ...},
    "payments": {"amount": {"data_type": "double"}, ...},
}

def _build_column_definitions(resource_name):
    return RESOURCE_COLUMNS.get(resource_name, {})
```

## Step 7: Validate

1. **Run the pipeline** with a single resource first
2. **Check loaded data** — row counts, column types, sample values
3. **Verify incremental state** — run again and confirm only new/modified records load
4. **Add the next resource** and repeat

```bash
# Run the pipeline
python my_pipeline.py --resources orders

# Inspect pipeline state
dlt pipeline my_pipeline show

# Use MCP server for validation (requires dlt[workspace])
dlt pipeline my_pipeline mcp
```

---

*Copyright (c) 2026 Swish BI Limited. All rights reserved.*
