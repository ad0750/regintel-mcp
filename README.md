# regintel-mcp

<!-- mcp-name: io.github.ad0750/regintel-mcp -->

[![PyPI version](https://img.shields.io/pypi/v/regintel-mcp.svg)](https://pypi.org/project/regintel-mcp/)
[![MCP Registry](https://img.shields.io/badge/MCP-Registry-blue)](https://registry.modelcontextprotocol.io/v0/servers/io.github.ad0750/regintel-mcp)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Drop-in regulatory data for your Claude agent.** Query 212+ regulations across 41 jurisdictions (GDPR, MiCA, DORA, AASB-S2, NGER, FATF, FCA, ASIC, MAS, SEC, FINRA…) with regulator citations. Works with Claude Desktop, Claude Code, and any MCP-compatible LLM client.

```bash
uvx regintel-mcp        # or: pip install regintel-mcp
```

**Smoke-test the install in 5 seconds** — `list_jurisdictions` works without an API key. Once you confirm the package is wired into your client, get a free key (100 credits, no card, ~20 seconds): **[regintelapi.com/k](https://regintelapi.com/k)**

## Tools

| Tool | What it does | Credits |
| --- | --- | --- |
| `list_jurisdictions` | All 41 supported jurisdictions with codes and regulation counts | **Free, no key required** |
| `search_regulations` | Filter the catalog by jurisdiction, tag, keyword, category. Paginated. | 1 |
| `get_regulation` | Full record (obligations, penalties, scope, source URL) for one regulation by ID | 1 |
| `get_recent_updates` | Regulations added or modified since a date. Useful for incremental sync of vector stores. | free |
| `check_compliance` | Decision signal (allowed / requires_license / restricted / prohibited) for an activity in a country | 1 |
| `get_aasb_s2_obligations` | Australian AASB-S2 climate-disclosure obligations. Filterable by Group tier, category code, reporting year. **Information only — does not calculate emissions or judge assurance.** | 1 |

## Configure with Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "regintel": {
      "command": "uvx",
      "args": ["regintel-mcp"],
      "env": {
        "REGINTEL_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Restart Claude Desktop. Six tools appear under the `regintel` server. Ask: *"is crypto trading allowed in Australia?"* — the model routes that to `check_compliance(country="AU", activity="crypto")` on its own.

## Configure with Claude Code

```bash
claude mcp add regintel -e REGINTEL_API_KEY=your-api-key-here -- uvx regintel-mcp
```

## Try it without a key

`list_jurisdictions` is auth-optional — useful as a sanity check after install:

> *Ask Claude:* "list the jurisdictions in the regintel server"

If you get back a JSON list with EU, US, AU, SG, UK and 36 others, the package is wired in. Now grab a key for the rest of the tools: [regintelapi.com/k](https://regintelapi.com/k)

## Environment variables

- `REGINTEL_API_KEY` *(required for billed tools)* — your API key. Without it, `list_jurisdictions` still works; every other tool returns an actionable signup prompt.
- `REGINTEL_API_BASE` *(optional)* — override the API base URL. Defaults to `https://api.regintelapi.com`.

## Pricing

| Plan | Credits | Price |
| --- | --- | --- |
| Free | 100 (one-time, no expiry) | $0, no card |
| Starter | 1,000/month | $10/month |
| Pro | 10,000/month | $50/month |

One-time credit packs also available. See [regintelapi.com/pricing](https://regintelapi.com/pricing.html).

## Links

- **Get a free key:** https://regintelapi.com/k
- **API docs:** https://regintelapi.com/docs.html
- **OpenAPI spec:** https://regintelapi.com/openapi.json
- **MCP Registry listing:** https://registry.modelcontextprotocol.io/v0/servers/io.github.ad0750/regintel-mcp
- **Source:** https://github.com/ad0750/regintel-mcp

## License

MIT
