"""RegIntel MCP server — exposes the RegIntel REST API as MCP tools."""

from __future__ import annotations

import json
import os
import sys
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

API_BASE = os.environ.get("REGINTEL_API_BASE", "https://api.regintelapi.com")
API_KEY = os.environ.get("REGINTEL_API_KEY", "")
USER_AGENT = "regintel-mcp/0.5.0"
TIMEOUT_SECONDS = 30.0

mcp = FastMCP("regintel")

# ─────────────────────────────────────────────────────────────────────────────
# Demo-mode helpers
# ─────────────────────────────────────────────────────────────────────────────
# When REGINTEL_API_KEY is not set, billed tools return a canned sample
# response showing the shape of real data (so the LLM can answer "what would
# the call look like?") together with a signup CTA. This is much friendlier
# than just returning an error — the user / LLM gets to *see* the value
# before being asked to commit.
#
# The demo response is clearly marked with `meta.demo_mode: true` and a
# `demo_notice` so downstream code can tell live data from sample.

DEMO_CTA = (
    "\n\n---\n"
    "★ The data above is a SAMPLE showing what a real response looks like.\n"
    "★ For live queries against all 212+ regulations across 41 jurisdictions,\n"
    "★ get a free API key (100 credits, no card, ~20 seconds):\n"
    "★   https://regintelapi.com/k\n"
    "★ Then set REGINTEL_API_KEY in your MCP client config and restart."
)


def _demo_response(body: dict[str, Any]) -> str:
    """Format a demo dict as the same JSON the live API would return, plus the CTA."""
    return json.dumps(body, indent=2, ensure_ascii=False) + DEMO_CTA


DEMO_SEARCH_REGULATIONS: dict[str, Any] = {
    "data": [
        {
            "id": 123,
            "uri": "https://api.regintelapi.com/regulations/123",
            "short_title": "GDPR — General Data Protection Regulation",
            "jurisdiction": "EU",
            "category": "Privacy",
            "tags": ["GDPR", "privacy", "data-protection"],
            "regulation": "Regulation (EU) 2016/679 on the protection of natural persons with regard to the processing of personal data.",
            "obligations": "Controllers must establish a lawful basis under Article 6 before processing personal data; document processing activities; notify breaches to the supervisory authority within 72 hours; honour data-subject rights (access, rectification, erasure, portability).",
            "penalties": "Administrative fines up to €20M or 4% of worldwide annual turnover (whichever is higher).",
            "scope": "Any organisation processing personal data of EU residents, regardless of where the organisation is established.",
            "source_url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
            "status": "active",
        },
        {
            "id": 126,
            "uri": "https://api.regintelapi.com/regulations/126",
            "short_title": "MiCA — Markets in Crypto-Assets Regulation",
            "jurisdiction": "EU",
            "category": "Crypto",
            "tags": ["MiCA", "crypto", "stablecoin"],
            "regulation": "Regulation (EU) 2023/1114 on markets in crypto-assets.",
            "obligations": "Crypto-asset service providers must obtain authorisation from a national competent authority; issuers of asset-referenced tokens must publish a whitepaper and maintain reserve assets equal to the value in circulation.",
            "penalties": "Up to €5M or 3% of annual turnover for legal persons; up to €700k for natural persons.",
            "scope": "All crypto-asset service providers operating in the EU.",
            "source_url": "https://eur-lex.europa.eu/eli/reg/2023/1114/oj",
            "status": "active",
        },
    ],
    "meta": {
        "total": 212,
        "page": 1,
        "limit": 20,
        "demo_mode": True,
        "demo_notice": "Sample data — real query would search across all 212 regulations matching your filter.",
    },
}


DEMO_GET_REGULATION: dict[str, Any] = {
    "data": {
        "id": 123,
        "uri": "https://api.regintelapi.com/regulations/123",
        "short_title": "GDPR — General Data Protection Regulation",
        "jurisdiction": "EU",
        "country": "EU",
        "category": "Privacy",
        "industry": "Privacy",
        "tags": ["GDPR", "privacy", "data-protection"],
        "regulation": "Regulation (EU) 2016/679 on the protection of natural persons with regard to the processing of personal data and on the free movement of such data.",
        "obligations": "Controllers must establish a lawful basis under Article 6 before processing personal data; perform DPIAs for high-risk processing; appoint a DPO where required; honour data-subject rights (access, rectification, erasure, restriction, portability, objection); notify the supervisory authority of breaches within 72 hours.",
        "penalties": "Administrative fines up to €20M or 4% of total worldwide annual turnover of the preceding financial year (whichever is higher).",
        "scope": "Any organisation processing personal data of individuals located in the EU, regardless of where the organisation is established.",
        "key_articles": "Art. 6 (lawful basis), Art. 17 (right to erasure), Art. 25 (privacy by design), Art. 33 (breach notification), Art. 35 (DPIA), Art. 83 (penalties)",
        "source_url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        "status": "active",
        "effective_date": "2018-05-25",
    },
    "meta": {
        "credits_used": 0,
        "demo_mode": True,
        "demo_notice": "Sample data for ID 123 (GDPR). Real call returns the full record for whichever ID you query.",
    },
}


DEMO_GET_RECENT_UPDATES: dict[str, Any] = {
    "data": [
        {
            "id": 325,
            "uri": "https://api.regintelapi.com/regulations/325",
            "short_title": "EDPB-EDPS Joint Opinion 2/2026 on Digital Omnibus GDPR Amendments",
            "jurisdiction": "EU",
            "category": "Privacy",
            "change_type": "new",
            "change_date": "2026-02-11",
            "source_url": "https://edpb.europa.eu/our-work-tools/our-documents/edpbedps-joint-opinion/joint-opinion-22026_en",
        },
        {
            "id": 318,
            "uri": "https://api.regintelapi.com/regulations/318",
            "short_title": "ASIC RG 280 Sustainability reporting — final guide",
            "jurisdiction": "AU",
            "category": "Finance",
            "change_type": "amended",
            "change_date": "2026-03-31",
            "source_url": "https://download.asic.gov.au/media/j4rhwyiz/rg280-published-31-march-2025.pdf",
        },
    ],
    "meta": {
        "demo_mode": True,
        "demo_notice": "Sample update feed. Real call returns regulations added/amended since the date you pass.",
    },
}


def _demo_check_compliance(country: str, activity: str) -> dict[str, Any]:
    """Build a check_compliance demo response that echoes the caller's args
    so the user can see what their actual query would have returned.
    The body intentionally reflects the input verbatim, not a real lookup."""
    return {
        "data": {
            "decision": "requires_license",
            "risk_level": "medium",
            "country": country,
            "activity": activity,
            "summary": f"Demo result: {activity} activity in {country} typically requires registration with the local regulator. The live endpoint returns the real decision plus the source regulations.",
            "obligations": [
                "Register the activity with the relevant local regulator before commencing operations",
                "Maintain an AML/CTF program proportionate to the activity",
                "Conduct customer due diligence (CDD) and ongoing monitoring",
            ],
            "penalties": "Up to 2 years imprisonment and/or substantial fines under local AML/CTF legislation (varies by jurisdiction).",
            "disclaimer": "NOT LEGAL ADVICE. Always consult a qualified legal professional in the relevant jurisdiction.",
            "source_regulations": [
                {"id": 123, "uri": "https://api.regintelapi.com/regulations/123", "title": "Example AML/CTF Act"},
            ],
        },
        "meta": {
            "demo_mode": True,
            "demo_notice": f"Sample decision for ({country}, {activity}). Real call returns the live decision derived from the structured rules.",
        },
    }


DEMO_GET_AASB_S2_OBLIGATIONS: dict[str, Any] = {
    "data": [
        {
            "id": 13,
            "requirement_code": "AASB-S2-REQ-013",
            "pillar": "metrics_targets",
            "category_code": "AASB-S2-MET-GHG-S3",
            "paragraph_ref": "¶29(a)(i)(3), (vi)",
            "title": "Scope 3 emissions",
            "obligation_text": "Disclose absolute gross Scope 3 emissions and state which of the 15 GHG-Protocol value-chain categories are included.",
            "type": "quantitative",
            "source_url": "https://standards.aasb.gov.au/aasb-s2-sep-2024",
            "applicability_per_group": {
                "group_1": {
                    "group_code": "group_1",
                    "group_label": "Group 1 — largest entities",
                    "first_reporting_period_start_date": "2025-01-01",
                    "applies": True,
                    "assurance_level": None,
                    "reliefs": [
                        {
                            "relief_type": "scope_3_year1_exemption",
                            "relief_summary": "Scope 3 disclosure not required in the entity's first annual reporting period under AASB S2.",
                            "relief_expiry": "2026-01-01",
                            "source_reference": "AASB S2 Appendix C4(b)",
                        }
                    ],
                }
            },
            "measurement_categories": [],
            "methodology_references": [],
            "assurance_inputs_required": [],
            "reporting_templates": [],
        }
    ],
    "meta": {
        "total": 26,
        "demo_mode": True,
        "demo_notice": "Sample obligation (Scope 3 emissions). Real call returns up to 26 obligations across the 4 AASB-S2 pillars with full per-Group applicability.",
        "advisory": "Information only. RegIntel does not calculate emissions, does not judge assurance, does not determine Chapter 2M scope or Group tier.",
    },
}


async def _request(
    path: str,
    params: dict[str, Any] | None = None,
    auth_required: bool = True,
    demo_response: dict[str, Any] | None = None,
) -> str:
    """GET helper that returns a string ready to hand back to the LLM.

    Errors are returned as plain-text messages rather than raised so the LLM
    sees an actionable explanation instead of a stack trace.

    auth_required=False is used by list_jurisdictions so a new installer can
    verify the package works before being asked to sign up.

    demo_response is used by billed tools when no API key is set: instead of
    failing with an error, the tool returns a canned sample showing the
    response shape, plus a signup CTA. The LLM sees the value first and is
    then asked to commit.
    """
    if auth_required and not API_KEY:
        if demo_response is not None:
            return _demo_response(demo_response)
        return (
            "RegIntel API key required for this tool.\n\n"
            "Get a free key — 100 credits, no card, ~20 seconds:\n"
            "  https://regintelapi.com/k\n\n"
            "Then set REGINTEL_API_KEY in your MCP client config and restart.\n\n"
            "Tip: list_jurisdictions works without a key, so you can verify the "
            "package is installed correctly before signing up."
        )

    url = f"{API_BASE}{path}"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if API_KEY:
        headers["x-api-key"] = API_KEY
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
        return (
            f"Error 401 (unauthorized): {message}.\n"
            "Check that REGINTEL_API_KEY is set correctly. If you don't have a key, "
            "get one in ~20 seconds at https://regintelapi.com/k"
        )
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
    This endpoint does not consume API credits AND does not require an API key — useful as a
    smoke test after installing the regintel-mcp package.
    """
    return await _request("/jurisdictions", auth_required=False)


@mcp.tool()
async def search_regulations(
    jurisdiction: str | None = None,
    tag: str | None = None,
    q: str | None = None,
    category: str | None = None,
    limit: int | None = None,
    page: int | None = None,
) -> str:
    """Search the RegIntel database of global regulatory and compliance rules.

    Use this tool when the user asks about regulatory obligations, compliance
    requirements, legal changes, cross-border regulatory differences, or
    industry-specific rules in any of 41 supported jurisdictions (e.g. GDPR
    and MiCA in the EU, MAS rules in Singapore, FCA in the UK, APRA/ASIC in
    Australia, SEC/FINRA in the US). Australian coverage now includes deep
    verticals: AASB-S2 climate disclosure (Chapter 2M reporting entities),
    Migration Act / Regulations / Skilled Occupation List instruments (for
    Registered Migration Agents meeting OMARA Code library obligations), and
    NDIS Act / Pricing Arrangements / Practice Standards / Code of Conduct
    (for registered NDIS providers and plan managers). Returns a paginated
    list of matching regulations; each result includes title, jurisdiction,
    category, tags, a summary, a canonical `uri`, and an upstream
    `source_url` (the original regulator's page) for citation. To get the
    full obligations/penalties/scope for a specific regulation, follow up
    with get_regulation(id).

    Args:
        jurisdiction: ISO-style jurisdiction code, e.g. "EU", "US", "AU", "SG", "UK". Optional.
        tag: Tag filter, e.g. "GDPR", "KYC", "AML", "crypto", "migration", "ndis", "pricing-arrangements", "aasb-s2". Optional.
        q: Free-text keyword search across regulation title and body. Optional.
        category: Category filter, e.g. "Privacy", "Finance", "Crypto", "AML". Optional.
        limit: Number of results per page (max 100). Optional.
        page: Page number for pagination, 1-indexed. Optional.
    """
    params = {
        "jurisdiction": jurisdiction,
        "tag": tag,
        "q": q,
        "category": category,
        "limit": limit,
        "page": page,
    }
    return await _request("/regulations", params=params, demo_response=DEMO_SEARCH_REGULATIONS)


@mcp.tool()
async def get_regulation(regulation_id: int) -> str:
    """Get the full record for a single regulation by its integer ID.

    Use this when the user asks for the specific obligations, penalties,
    scope, or article-level detail of a named regulation (e.g. "what are
    the obligations under GDPR?", "what's the penalty range for MiCA?",
    "summarise Article 17 of GDPR"). Returns the complete regulation
    document: jurisdiction (and legacy `country`), category (and legacy
    `industry`), regulation text, obligations, penalties, scope, tags,
    upstream `source_url`, canonical `uri`, key articles, and timestamps.

    IDs are integers (e.g. 123 = GDPR, 124 = GDPR Art. 17, 126 = MiCA).
    Use search_regulations first to discover IDs — every result includes
    an `id` field you can pass here.

    Args:
        regulation_id: Integer ID of the regulation, e.g. 123. Required.
    """
    return await _request(f"/regulations/{regulation_id}", demo_response=DEMO_GET_REGULATION)


@mcp.tool()
async def get_recent_updates(
    since: str | None = None,
    jurisdiction: str | None = None,
) -> str:
    """List regulations added or amended recently — the regulatory change feed.

    Use this when the user asks "what's new in [jurisdiction] compliance",
    "what regulations changed this quarter", "are there any recent updates
    to MiCA / GDPR / etc.", or for incremental sync of a downstream cache
    or vector store (only re-process what changed). Each item carries a
    canonical `uri`, an upstream `source_url`, and a `change_type` of
    `new` or `amended`.

    Args:
        since: ISO date (YYYY-MM-DD) lower bound for the modification timestamp, e.g. "2026-01-01".
            If omitted, the API returns the default recent window.
        jurisdiction: Optional jurisdiction code to scope the query, e.g. "EU".
    """
    return await _request(
        "/updates",
        params={"since": since, "jurisdiction": jurisdiction},
        demo_response=DEMO_GET_RECENT_UPDATES,
    )


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
    return await _request(
        "/compliance-check",
        params={"country": country, "activity": activity},
        demo_response=_demo_check_compliance(country, activity),
    )


@mcp.tool()
async def get_aasb_s2_obligations(
    group: int | None = None,
    category_code: str | None = None,
    reporting_year: int | None = None,
) -> str:
    """List Australian AASB-S2 (Climate-related Financial Disclosures) disclosure obligations
    applicable to a covered entity, with calculator-ready annotations.

    INFORMATION ONLY. This tool returns the disclosure obligations imposed by AASB-S2 — what
    an entity must say in its sustainability report — together with calculator-ready
    annotation fields that a downstream sustainability calculation product (Persefoni,
    Watershed, Sweep, in-house tooling) can consume to know WHAT to measure and WHERE the
    authoritative methodology lives. RegIntel does NOT calculate emissions, does NOT judge
    assurance, does NOT determine Chapter 2M scope, and does NOT determine which Group tier
    an entity falls into. For actual emissions calculation, use a specialist calculator
    product — the response includes methodology_references pointing at the standards those
    products should be implementing.

    Use this when the user asks: "what does AASB-S2 require?", "what Scope 3 disclosures
    apply to my Australian company?", "when does AASB-S2 review/audit start for Group 2 /
    Group 3 entities?", "what governance disclosures are required under AASB-S2?", or when
    an AI agent is helping a calculator product team scope their methodology against AASB-S2
    obligations.

    Each obligation entry includes the disclosure category, paragraph references, applicability
    per Group tier (per ASIC RG 280 Sustainability Reporting), effective date considering
    phase-in relief, assurance level (limited/review vs reasonable/audit per AUASB ASSA 5000
    and the ASSA 5010 phase-in timetable), source URL to the AASB-S2 standard, the explicit
    ASIC regulatory context, AND four calculator-ready annotation fields:
    `measurement_categories` (what to compute), `methodology_references` (authoritative
    how-to sources — GHG Protocol, ISO 14064-1, NGER Determination, etc.),
    `assurance_inputs_required` (evidence the ASSA 5000 assurance practitioner will demand),
    and `reporting_templates` (industry-specific reporting structure where applicable).
    Every response carries an advisory string in `meta.advisory` reaffirming the
    information-only boundary.

    Args:
        group: Filter by entity Group tier (1 = largest entities reporting from FY commencing
            1 Jan 2025; 2 = mid-tier from 1 Jul 2026; 3 = smaller from 1 Jul 2027). The tool
            does NOT determine which Group an entity is in — the caller must classify based
            on the entity's facts (employee count, revenue, gross assets, NGER status).
        category_code: Filter to specific disclosure category, e.g. "AASB-S2-MET-GHG-S3" for
            Scope 3 emissions, "AASB-S2-GOV" for governance. Optional. See the 13 category
            codes in the API documentation.
        reporting_year: Reporting year of interest (e.g. 2026). When supplied, the response
            indicates whether each obligation is applicable that year given phase-in relief
            and what assurance level applies.
    """
    params = {
        "group": group,
        "category_code": category_code,
        "reporting_year": reporting_year,
    }
    return await _request(
        "/v1/aasb-s2/obligations",
        params=params,
        demo_response=DEMO_GET_AASB_S2_OBLIGATIONS,
    )


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
