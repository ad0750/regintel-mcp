# regintel-mcp

<!-- mcp-name: io.github.ad0750/regintel-mcp -->

MCP server for the [RegIntel API](https://regintelapi.com/) — structured regulatory data across 41 jurisdictions and 212+ regulations, with regulator citations. Works with any MCP-compatible LLM client (Claude Desktop, Claude Code, etc.).

**Requires a free API key** from [regintelapi.com/get-key](https://regintelapi.com/get-key.html) — 100 credits, no credit card required. Set as `REGINTEL_API_KEY` in your MCP client config (example below).

## Tools

| Tool | Description |
| --- | --- |
| `list_jurisdictions` | All 41 supported jurisdictions with codes and regulation counts. Does not consume credits. |
| `search_regulations` | Filter the catalog by jurisdiction, tag, keyword, category. Paginated. |
| `get_regulation` | Full record (obligations, penalties, scope, source URL) for one regulation by ID. |
| `get_recent_updates` | Regulations added or modified since a date. Useful for keeping vector stores in sync. |
| `check_compliance` | Decision signal (allowed / requires_license / restricted / prohibited) for an activity in a country. |

## Install

```bash
pip install regintel-mcp
```

## Get an API key

Free tier includes 100 credits with no expiry and no credit card: https://regintelapi.com/get-key.html

## Configure with Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "regintel": {
      "command": "regintel-mcp",
      "env": {
        "REGINTEL_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Restart Claude Desktop. The five tools above should appear under the regintel server.

## Configure with Claude Code

```bash
claude mcp add regintel -e REGINTEL_API_KEY=your-api-key-here -- regintel-mcp
```

## Environment variables

- `REGINTEL_API_KEY` *(required)* — your API key. Without it, every tool call returns an actionable error message.
- `REGINTEL_API_BASE` *(optional)* — override the API base URL. Defaults to `https://api.regintelapi.com`.

## License

MIT
