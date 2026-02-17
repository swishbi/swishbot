"""
Generic SQL Database Pipeline
==============================
Covers two patterns for loading data from SQL databases:

1. **Direct DB connection** — uses dlt's `sql_database` verified source to
   connect directly to a database and load tables/queries.
2. **SQL-over-REST** — for APIs that expose a SQL query interface (e.g.
   NetSuite SuiteQL, QuickBooks query endpoint). Uses custom auth, custom
   paginators, and dynamically generates resources from .sql files.

"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

import dlt
from dlt.sources.helpers.requests import Response
from dlt.sources.helpers.rest_client.paginators import BasePaginator

logger = logging.getLogger("dlt")


# ===========================================================================
# Pattern 1: Direct Database Connection
# ===========================================================================

def direct_db_source() -> None:
    """Load tables directly from a SQL database using dlt's sql_database source.

    Requires: pip install "dlt[sql_database]"
    Supports: PostgreSQL, MySQL, MSSQL, Oracle, SQLite, and any SQLAlchemy-compatible DB.

    Key options:
    - backend: "sqlalchemy" (default), "pyarrow" (faster for large tables),
               "connectorx" (fastest, requires connectorx package)
    - table_names: List of specific tables to load (None = all tables)
    - schema: Database schema to read from
    - incremental: Column-based incremental loading via dlt.sources.incremental
    """
    from dlt.sources.sql_database import sql_database

    # Connection string from environment — never hardcode credentials
    connection_string = os.getenv(
        "SOURCE_DB_CONNECTION_STRING",
        "postgresql://user:password@host:5432/database",
    )

    source = sql_database(
        credentials=connection_string,
        schema="public",
        table_names=["customers", "orders", "products"],
        # backend="pyarrow",  # Uncomment for large tables
    )

    # --- Incremental loading on a specific table ---
    # Apply incremental to the orders resource using the updated_at column.
    # dlt tracks the max value of updated_at and only loads newer rows on
    # subsequent runs.
    source.customers.apply_hints(
        incremental=dlt.sources.incremental("updated_at"),
        write_disposition="merge",
        primary_key="customer_id",
    )

    source.orders.apply_hints(
        incremental=dlt.sources.incremental("updated_at"),
        write_disposition="merge",
        primary_key="order_id",
    )

    # --- Column type hints for ambiguous types ---
    # Some databases return numeric fields as strings or use imprecise types.
    # Add explicit column hints to ensure correct types in the destination.
    source.orders.apply_hints(
        columns={
            "total_amount": {"data_type": "double", "nullable": True},
            "discount": {"data_type": "double", "nullable": True},
            "order_date": {"data_type": "date", "nullable": True},
        }
    )

    # --- Reference tables with full replace ---
    source.products.apply_hints(
        write_disposition="replace",
    )

    pipeline = dlt.pipeline(
        pipeline_name="sql_database_pipeline",
        destination="postgres",  # Replace with your destination
        dataset_name="raw_db",
        progress="log",
    )

    load_info = pipeline.run(source)
    print(load_info)


# ===========================================================================
# Pattern 2: SQL-over-REST (e.g. NetSuite SuiteQL, custom query APIs)
# ===========================================================================

# --- Custom OAuth1 auth for APIs that require it (e.g. NetSuite TBA) ---
#
# from requests_oauthlib import OAuth1
# from dlt.sources.helpers.rest_client.auth import AuthBase
#
# class OAuth1Auth(AuthBase):
#     def __init__(self, consumer_key, consumer_secret, token, token_secret,
#                  realm=None):
#         self.oauth = OAuth1(
#             client_key=consumer_key,
#             client_secret=consumer_secret,
#             resource_owner_key=token,
#             resource_owner_secret=token_secret,
#             realm=realm,
#             signature_method="HMAC-SHA1",
#         )
#
#     def __call__(self, request):
#         request.auth = self.oauth
#         return request


class RowNumPaginator(BasePaginator):
    """Paginator for SQL APIs that use ROWNUM/OFFSET in query results.

    Wraps each SQL query with a row-number window and paginates through
    results in fixed-size pages. Use for APIs that don't provide cursor-based
    pagination but accept SQL queries (e.g. NetSuite SuiteQL).

    Pattern: Wraps the user's SQL as a subquery and adds
    WHERE rownum BETWEEN :start AND :end
    """

    def __init__(self, page_size: int = 1000):
        super().__init__()
        self.page_size = page_size
        self._offset = 0

    def init_request(self, request) -> None:
        request.params["offset"] = self._offset
        request.params["limit"] = self.page_size

    def update_state(self, response: Response, data: Optional[List[Any]] = None) -> None:
        if not data or len(data) < self.page_size:
            self._has_next_page = False
        else:
            self._offset += self.page_size

    def update_request(self, request) -> None:
        request.params["offset"] = self._offset
        request.params["limit"] = self.page_size


def read_sql_files(sql_dir: Path) -> Dict[str, str]:
    """Read all .sql files from a directory and return {table_name: sql_query}.

    Convention: filename (without extension) becomes the resource/table name.
    Files starting with '_' are skipped (inactive/draft queries).
    """
    queries = {}
    for sql_file in sorted(sql_dir.glob("*.sql")):
        if sql_file.stem.startswith("_"):
            continue
        queries[sql_file.stem] = sql_file.read_text()
    return queries


@dlt.source(name="sql_over_rest_example", max_table_nesting=0)
def sql_over_rest_source(
    api_base_url: str = dlt.config.value,
    api_token: str = dlt.secrets.value,
) -> Iterator[Any]:
    """Source that executes SQL queries against a REST API endpoint.

    Dynamically generates one dlt resource per .sql file found in the
    sql/ directory. Each resource executes its query through the API and
    paginates through the results.

    This pattern is used for:
    - NetSuite SuiteQL (POST queries to /suiteql endpoint)
    - Any API that accepts SQL/query strings and returns paginated results
    """
    from dlt.sources.helpers.rest_client.client import RESTClient

    sql_dir = Path(__file__).parent / "sql"
    queries = read_sql_files(sql_dir)

    if not queries:
        logger.warning(f"No .sql files found in {sql_dir}")
        return

    client = RESTClient(
        base_url=api_base_url,
        headers={
            "Content-Type": "application/json",
            "Prefer": "transient",  # Read-only queries (NetSuite pattern)
        },
        # auth=OAuth1Auth(...)  # Use your auth method
    )

    paginator = RowNumPaginator(page_size=1000)

    for table_name, query in queries.items():

        @dlt.resource(
            name=table_name,
            write_disposition="replace",
            max_table_nesting=0,
        )
        def _query_resource(
            _query: str = query,
            _client: RESTClient = client,
            _paginator: RowNumPaginator = paginator,
        ) -> Iterator[List[Dict[str, Any]]]:
            """Execute a SQL query against the API and yield paginated results."""
            offset = 0
            page_size = _paginator.page_size

            while True:
                response = _client.session.post(
                    f"{_client.base_url}/query",
                    json={"q": _query},
                    params={"offset": offset, "limit": page_size},
                )
                response.raise_for_status()
                items = response.json().get("items", [])

                if not items:
                    break

                yield items

                if len(items) < page_size:
                    break
                offset += page_size

        yield _query_resource


# ---------------------------------------------------------------------------
# Pipeline runner
# ---------------------------------------------------------------------------

def load_sql_over_rest() -> None:
    source = sql_over_rest_source()

    pipeline = dlt.pipeline(
        pipeline_name="sql_over_rest_pipeline",
        destination="postgres",  # Replace with your destination
        dataset_name="raw_sql",
        progress="log",
    )

    load_info = pipeline.run(source)
    print(load_info)


if __name__ == "__main__":
    # Choose which pattern to run:
    # direct_db_source()
    load_sql_over_rest()
