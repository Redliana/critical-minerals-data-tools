# Google Scholar MCP

MCP server for searching Google Scholar through `cmm-data`'s `GoogleScholarClient`.

## Why this package exists

- Keeps MCP transport/interface logic in `critical-minerals-data-tools`
- Keeps source data retrieval/client logic in `cmm-data`
- Avoids local `sys.path` hacks and sibling-directory imports

## Installation

```bash
cd GoogleScholar_MCP
uv sync
```

## Configuration

Set your SerpAPI key:

```bash
export SERPAPI_KEY="your-key"
```

## Run

```bash
uv run google-scholar-mcp
```

## Tools

- `search_scholar`

## Claude Desktop config

```json
{
  "mcpServers": {
    "google-scholar": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/GoogleScholar_MCP",
        "run",
        "google-scholar-mcp"
      ],
      "env": {
        "SERPAPI_KEY": "your-key"
      }
    }
  }
}
```
