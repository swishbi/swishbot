"""
Generic REST API Pipeline
==========================
Comprehensive example covering authentication, custom pagination, column typing,
incremental loading, processing steps, and multi-tenant support.

Synthesized from production patterns across multiple REST API sources.
"""

import argparse
import logging
import os
from typing import Any

import dlt
from dlt.common import pendulum
from dlt.sources.helpers.requests import Response
from dlt.sources.helpers.rest_client.paginators import BasePaginator
from dlt.sources.rest_api import rest_api_resources
from dlt.sources.rest_api.config_setup import register_paginator
from dlt.sources.rest_api.typing import RESTAPIConfig

logger = logging.getLogger("dlt")


# ---------------------------------------------------------------------------
# Authentication helpers
# ---------------------------------------------------------------------------

def get_auth_config(auth_type: str, **kwargs) -> dict[str, Any]:
    """Return the right dlt auth config based on the API's auth method.

    Args:
        auth_type: One of "bearer", "api_key", "oauth2_client_credentials".
        **kwargs: Auth-specific parameters (token, api_key, header_name, etc.).

    Built-in dlt auth types:
        - "bearer": BearerTokenAuth — sends Authorization: Bearer <token>
        - "api_key": APIKeyAuth — sends a key in a header or query param
        - "http_basic": HTTPBasicAuth — sends Authorization: Basic <base64>
        - "oauth2_client_credentials": OAuth2ClientCredentials — fetches a
          token from a token endpoint using client_id/client_secret

    For non-standard OAuth flows (e.g. custom login endpoints, tokens nested
    in response bodies), subclass OAuth2ClientCredentials — see the custom
    OAuth2 example below.
    """
    if auth_type == "bearer":
        return {
            "type": "bearer",
            "token": kwargs.get("token", os.getenv("API_TOKEN", "")),
        }

    if auth_type == "api_key":
        return {
            "type": "api_key",
            "name": kwargs.get("header_name", "X-API-Key"),
            "api_key": kwargs.get("api_key", os.getenv("API_KEY", "")),
            "location": kwargs.get("location", "header"),  # "header" or "query"
        }

    if auth_type == "oauth2_client_credentials":
        # Standard OAuth2 client_credentials grant
        return {
            "type": "oauth2_client_credentials",
            "access_token_url": kwargs["token_url"],
            "client_id": kwargs.get("client_id", os.getenv("OAUTH_CLIENT_ID", "")),
            "client_secret": kwargs.get("client_secret", os.getenv("OAUTH_CLIENT_SECRET", "")),
        }

    raise ValueError(f"Unknown auth_type: {auth_type}")


# Custom OAuth2 for APIs that don't follow the standard grant flow.
# Example: POST to a login endpoint with custom body, token nested in response.
#
# from dlt.sources.helpers.rest_client.auth import OAuth2ClientCredentials
#
# class CustomOAuth2(OAuth2ClientCredentials):
#     def build_access_token_request(self) -> Dict[str, Any]:
#         return {
#             "url": self.access_token_url,
#             "headers": {"Content-Type": "application/json"},
#             "json": {
#                 "partnerId": self.client_id,
#                 "authKey": self.client_secret,
#             },
#         }
#
#     def parse_access_token(self, response) -> str:
#         return response.json()["data"]["accessToken"]


# ---------------------------------------------------------------------------
# Custom paginators
# ---------------------------------------------------------------------------

class PageNumberTotalCountPaginator(BasePaginator):
    """Page-number paginator that stops when current_count >= total_count.

    Use when the API returns a total record count in the response body rather
    than a next-page link. Pattern extracted from AccuLynx, CenterPoint.
    """

    def __init__(self, page_size: int = 50, page_param: str = "page",
                 total_path: str = "count"):
        super().__init__()
        self.page_size = page_size
        self.page_param = page_param
        self.total_path = total_path
        self._page = 1

    def init_request(self, request) -> None:
        request.params[self.page_param] = self._page

    def update_state(self, response: Response, data: list[Any] | None = None) -> None:
        total = response.json().get(self.total_path, 0)
        current_count = self._page * self.page_size
        if not data or len(data) < self.page_size or current_count >= total:
            self._has_next_page = False
        else:
            self._page += 1

    def update_request(self, request) -> None:
        request.params[self.page_param] = self._page


# Register so it can be referenced by name in RESTAPIConfig
register_paginator("page_number_total_count", PageNumberTotalCountPaginator)


class CursorPaginator(BasePaginator):
    """Cursor-based paginator for APIs that return a cursor/token for the next page.

    Use when the API returns a field like "nextCursor", "offset", or "lastId"
    in the response body. Pattern extracted from JobNimbus.
    """

    def __init__(self, cursor_path: str = "nextCursor",
                 cursor_param: str = "cursor"):
        super().__init__()
        self.cursor_path = cursor_path
        self.cursor_param = cursor_param
        self._cursor: str | None = None

    def init_request(self, request) -> None:
        if self._cursor:
            request.params[self.cursor_param] = self._cursor

    def update_state(self, response: Response, data: list[Any] | None = None) -> None:
        self._cursor = response.json().get(self.cursor_path)
        if not self._cursor or not data:
            self._has_next_page = False

    def update_request(self, request) -> None:
        if self._cursor:
            request.params[self.cursor_param] = self._cursor


register_paginator("cursor", CursorPaginator)


# ---------------------------------------------------------------------------
# Column type definitions
# ---------------------------------------------------------------------------

# Explicit column hints prevent dlt from inferring wrong types (e.g. a numeric
# string like "100.00" inferred as text, or a date field stored as text).
# Define per-resource and reference in the resource config's "columns" key.

RESOURCE_COLUMNS: dict[str, dict[str, dict[str, Any]]] = {
    "invoices": {
        "total_amount": {"data_type": "double", "nullable": True},
        "balance": {"data_type": "double", "nullable": True},
        "due_date": {"data_type": "timestamp", "nullable": True},
        "created_date": {"data_type": "timestamp", "nullable": True},
    },
    "payments": {
        "amount": {"data_type": "double", "nullable": True},
        "payment_date": {"data_type": "timestamp", "nullable": True},
    },
    "orders": {
        "total": {"data_type": "double", "nullable": True},
        "order_date": {"data_type": "timestamp", "nullable": True},
    },
}


def _build_column_definitions(resource_name: str) -> dict[str, dict[str, Any]]:
    """Return column type hints for a resource, or empty dict if none defined."""
    return RESOURCE_COLUMNS.get(resource_name, {})


# ---------------------------------------------------------------------------
# Incremental loading helpers
# ---------------------------------------------------------------------------

def _build_incremental_config(
    cursor_path: str,
    initial_value: str = "2020-01-01T00:00:00Z",
    lag_days: int = 0,
    convert=None,
) -> dict[str, Any]:
    """Build an incremental loading config for a resource endpoint.

    Args:
        cursor_path: JSON path to the field used for tracking (e.g. "modifiedDate").
        initial_value: Starting value for first run.
        lag_days: Number of days to subtract from the cursor value to catch
                  late-arriving records. Set > 0 for APIs with eventual consistency.
        convert: Optional callable to normalize the cursor value
                 (e.g. parse ISO date to YYYY-MM-DD).
    """
    config: dict[str, Any] = {
        "cursor_path": cursor_path,
        "initial_value": initial_value,
    }
    if lag_days > 0:
        config["lag"] = lag_days
    if convert:
        config["convert"] = convert
    return config


# ---------------------------------------------------------------------------
# Processing steps (metadata injection, filtering, transformation)
# ---------------------------------------------------------------------------

def add_tenant_metadata(tenant_id: str, tenant_name: str):
    """Return a map function that injects tenant context into each record.

    Use for multi-tenant pipelines where data from different tenants is loaded
    into the same table. Add as a processing step or via resource.add_map().
    """
    def _add_metadata(record: dict[str, Any]) -> dict[str, Any]:
        record["_tenant_id"] = tenant_id
        record["_tenant_name"] = tenant_name
        return record
    return _add_metadata


# Filter example: skip records that are soft-deleted
# {"filter": lambda record: record.get("is_active", True)}

# Yield-map example: flatten nested arrays into individual records
# {"yield_map": lambda record: (
#     {**record, "line_item": item}
#     for item in record.pop("line_items", [])
# )}


# ---------------------------------------------------------------------------
# Source definition
# ---------------------------------------------------------------------------

@dlt.source(name="rest_api_example", root_key=True, max_table_nesting=0)
def rest_api_source(
    api_token: str = dlt.secrets.value,
    tenant_id: str = dlt.config.value,
    tenant_name: str = dlt.config.value,
) -> Any:
    """Generic REST API source.

    Demonstrates:
    - Bearer token auth (swap get_auth_config call for your auth method)
    - Custom paginator registration and usage
    - Column type hints per resource
    - Incremental loading with date cursor and lag
    - Processing steps for metadata injection and filtering
    - Parent-child (dependent) resources
    - Parallelized child resources
    - SCD2 write disposition for slowly-changing reference data
    """
    metadata_fn = add_tenant_metadata(tenant_id, tenant_name)

    config: RESTAPIConfig = {
        "client": {
            "base_url": os.getenv("API_BASE_URL", "https://api.example.com/v2/"),
            "headers": {
                "Accept": "application/json",
                "User-Agent": "dlt-pipeline/1.0",
            },
            "auth": get_auth_config("bearer", token=api_token),
            "paginator": {
                "type": "page_number_total_count",
                "page_size": 50,
                "total_path": "totalCount",
            },
        },
        "resource_defaults": {
            "primary_key": ["id", "_tenant_id"],
            "merge_key": "_tenant_id",
            "write_disposition": {"disposition": "merge", "strategy": "delete-insert"},
            "endpoint": {
                "method": "GET",
                "data_selector": "items",
            },
            "processing_steps": [
                {"map": metadata_fn},
            ],
        },
        "resources": [
            # --- Simple endpoint with incremental loading ---
            {
                "name": "orders",
                "columns": _build_column_definitions("orders"),
                "endpoint": {
                    "path": "orders",
                    "params": {
                        "modifiedSince": "{incremental.start_value}",
                        "modifiedBefore": pendulum.now().isoformat(),
                        "sortBy": "modifiedDate",
                    },
                    "incremental": _build_incremental_config(
                        cursor_path="modifiedDate",
                        initial_value="2020-01-01T00:00:00Z",
                        lag_days=3,
                        convert=lambda dt: pendulum.parse(dt).format("YYYY-MM-DDTHH:mm:ss[Z]"),
                    ),
                },
            },
            # --- Endpoint with custom paginator ---
            {
                "name": "invoices",
                "columns": _build_column_definitions("invoices"),
                "endpoint": {
                    "path": "invoices",
                    "paginator": {
                        "type": "cursor",
                        "cursor_path": "meta.nextCursor",
                        "cursor_param": "after",
                    },
                },
            },
            # --- Parent-child resources (dependent) ---
            {
                "name": "customers",
                "parallelized": True,
                "endpoint": {
                    "path": "customers",
                },
            },
            {
                "name": "customer_contacts",
                "parallelized": True,
                "endpoint": {
                    "path": "customers/{resources.customers.id}/contacts",
                    "data_selector": "$",
                    "paginator": {"type": "single_page"},
                },
                "include_from_parent": ["id"],
                "primary_key": ["_customers_id", "contact_id", "_tenant_id"],
                "merge_key": ["_customers_id", "_tenant_id"],
            },
            # --- Reference table with SCD2 ---
            {
                "name": "categories",
                "write_disposition": {"disposition": "merge", "strategy": "scd2"},
                "endpoint": {
                    "path": "categories",
                    "paginator": {"type": "single_page"},
                    "data_selector": "$",
                },
            },
            # --- Endpoint with filter processing step ---
            {
                "name": "payments",
                "columns": _build_column_definitions("payments"),
                "endpoint": {
                    "path": "payments",
                },
                "processing_steps": [
                    {"map": metadata_fn},
                    {"filter": lambda record: record.get("status") != "voided"},
                ],
            },
        ],
    }

    yield from rest_api_resources(config)


# ---------------------------------------------------------------------------
# Pipeline runner with CLI args and multi-tenant support
# ---------------------------------------------------------------------------

def parse_arguments():
    parser = argparse.ArgumentParser(description="REST API pipeline")
    parser.add_argument("--resources", nargs="+", help="Resources to load")
    parser.add_argument("--tenants", nargs="+", help="Tenant IDs to load")
    return parser.parse_args()


def load_rest_api() -> None:
    args = parse_arguments()
    tenants = args.tenants or os.getenv("PIPELINE_TENANTS", "default").split(",")

    for tenant in tenants:
        source = rest_api_source(
            api_token=dlt.secrets[f"{tenant}.api_token"],
            tenant_id=tenant,
            tenant_name=tenant,
        )

        if args.resources:
            source = source.with_resources(*args.resources)

        pipeline = dlt.pipeline(
            pipeline_name=f"rest_api_pipeline_{tenant}",
            destination="postgres",  # Replace with your destination
            dataset_name="raw_api",
            progress="log",
        )

        load_info = pipeline.run(source)
        print(load_info)


if __name__ == "__main__":
    load_rest_api()
