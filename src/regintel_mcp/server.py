"""RegIntel MCP server — exposes the RegIntel REST API as MCP tools."""

from __future__ import annotations

import os
import sys
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

API_BASE = os.environ.get("REGINTEL_API_BASE", "https://api.regintelapi.com")
API_KEY = os.environ.get("REGINTEL_API_KEY", "")
USER_AGENT = "regintel-mcp/0.1.0"
TIMEOUT_SECONDS = 30.0

mcp = FastMCP("regintel")


async def _request(path: str, params: dict[str, Any] | None = None) -> str:
    """GET helper that returns a string ready to hand back to the LLM.

    Errors are returned as plain-text messages rather than raised so the LLM
    sees an actionable explanation instead of a stack trace.
    """
    if not API_KEY:
        return (
            "Error: REGINTEL_API_KEY environment variable is not set. "
            "Get a free API key at https://regintelapi.com/get-key.html and set "
            "REGINTEL_API_KEY in your MCP client configuration."
        )

    url = f"{API_BASE}{path}"
    headers = {"x-api-key": API_KEY, "User-Agent": USER_AGENT, "Accept": "application/json"}
    cleaned = {k: v for k, v in (params or {}).items() if v is not None and v != ""}

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.get(url, headers=headers, params=cleaned)
    except httpx.TimeoutException:
        return f"Error: request to {path} timed out after {TIMEOUT_SECONDS}s."
    except httpx.HTTPError as exc:
        return f"Error: network failure calling {path}: {exc}"

    if response.status_code == 200:
        return response.text

    try:
        body = response.json()
        message = body.get("message") or body.get("error") or response.text
    except Exception:
        message = response.text

    if response.status_code == 401:
        return f"Error 401 (unauthorized): {message}. Check that REGINTEL_API_KEY is correct."
    if response.status_code == 403:
        return (
            f"Error 403 (forbidden): {message}. You may be out of credits — "
            "check https://regintelapi.com/dashboard.html or top up at /pricing.html."
        )
    if response.status_code == 404:
        return f"Error 404 (not found): {message}"
    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After", "unknown")
        return f"Error 429 (rate limited): retry after {retry_after}s."
    return f"Error {response.status_code}: {message}"


@mcp.tool()
async def list_jurisdictions() -> str:
    """List all regulatory jurisdictions supported by RegIntel, with their codes and regulation counts.

    Use this to discover the universe of supported regions (currently 41) and the canonical
    jurisdiction codes you can pass to other tools like search_regulations or check_compliance.
    This endpoint does not consume API credits.
    """
    return await _request("/jurisdictions")


@mcp.tool()
async def search_regulations(
    jurisdiction: str | None = None,
    tag: str | None = None,
    q: str | None = None,
    category: str | None = None,
    limit: int | None = None,
    page: int | None = None,
) -> str:
    """Search the regulation catalog. Returns a paginated list of regulations matching the filters.

    Each result includes title, jurisdiction, category, tags, and a summary. To get the full
    obligations/penalties/scope for a specific regulation, follow up with get_regulation(id).

    Args:
        jurisdiction: ISO-style jurisdiction code, e.g. "EU", "US", "AU", "SG", "UK". Optional.
        tag: Tag filter, e.g. "GDPR", "KYC", "AML", "crypto". Optional.
        q: Free-text keyword search across regulation title and body. Optional.
        category: Category filter (e.g. "data_protection", "payments"). Optional.
        limit: Number of results per page. Optional.
        page: Page number for pagination. Optional.
    """
    params = {
        "jurisdiction": jurisdiction,
        "tag": tag,
        "q": q,
        "category": category,
        "limit": limit,
        "page": page,
    }
    return await _request("/regulations", params=params)


@mcp.tool()
async def get_regulation(regulation_id: str) -> str:
    """Get the full record for a single regulation by its unique ID.

    Returns the complete regulation document: title, jurisdiction, obligations, penalties,
    scope, tags, source URL, key articles, and timestamps. Use search_regulations first to
    discover IDs.

    Args:
        regulation_id: Regulation ID, e.g. "gdpr-2018". Required.
    """
    if not regulation_id:
        return "Error: regulation_id is required."
    return await _request(f"/regulations/{regulation_id}")


@mcp.tool()
async def get_recent_updates(
    since: str | None = None,
    jurisdiction: str | None = None,
) -> str:
    """List regulations added or modified recently. Use this to keep a downstream cache or
    vector store in sync — only re-process what changed.

    Args:
        since: ISO date (YYYY-MM-DD) lower bound for the modification timestamp, e.g. "2026-01-01".
            If omitted, the API returns the default recent window.
        jurisdiction: Optional jurisdiction code to scope the query, e.g. "EU".
    """
    return await _request("/updates", params={"since": since, "jurisdiction": jurisdiction})


@mcp.tool()
async def check_compliance(country: str, activity: str) -> str:
    """Check the regulatory status of an activity in a country. Returns a decision signal —
    one of `allowed`, `requires_license`, `restricted`, `prohibited`, or `unknown` — along
    with risk level, penalties, obligations, and the source regulations behind the decision.

    NOT LEGAL ADVICE. This endpoint provides regulatory intelligence derived from structured
    data; always consult a qualified legal professional before acting on it.

    Args:
        country: Country code or name, e.g. "AU", "US", "EU", "SG", "UK". Required.
        activity: One of "crypto", "finance", "banking", "payments", "lending", "privacy",
            "data_protection", "aml", "kyc". Required.
    """
    if not country or not activity:
        return "Error: both 'country' and 'activity' are required."
    return await _request("/compliance-check", params={"country": country, "activity": activity})


def main() -> None:
    print(f"regintel-mcp starting (API base: {API_BASE})", file=sys.stderr)
    if not API_KEY:
        print(
            "Warning: REGINTEL_API_KEY is not set; tool calls will return an error until it is.",
            file=sys.stderr,
        )
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
