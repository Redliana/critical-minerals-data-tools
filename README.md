# Critical Minerals Data Tools

A suite of MCP servers and supporting APIs for accessing critical minerals and materials data from authoritative sources. Designed for AI-powered analysis, supply chain research, and LLM integration.

## Data Sources

| Source | Description | Coverage | Data Types |
|--------|-------------|----------|------------|
| **CLAIMM (NETL EDX)** | US Critical Minerals and Materials | 200+ datasets | Research data, CSV, schemas |
| **BGS World Mineral Statistics** | Global mineral production & trade | 1970-2023, 70+ minerals | Production, imports, exports |

## Projects Overview

```
Data_Needs/
├── CLaiMM/          # CLAIMM MCP servers (standard + agnostic)
├── BGS_MCP/         # BGS MCP server + REST API
├── CMM_API/         # Legacy unified API (deprecated)
└── README.md        # This file
```

### Quick Comparison

| Project | Interface | Data Source | LLM Required | Best For |
|---------|-----------|-------------|--------------|----------|
| **CLaiMM** (standard) | MCP | CLAIMM | Yes | AI-powered search with summarization |
| **CLaiMM** (agnostic) | MCP | CLAIMM | No | Direct CLAIMM data access |
| **BGS_MCP** | MCP + REST | BGS | No | Global production statistics |
| **CMM_API (legacy)** | MCP + REST | Both | No | Backward compatibility only |

## Choosing the Right Tool

### For Claude Desktop / Claude Code Users

| Need | Recommended | Command |
|------|-------------|---------|
| US datasets + AI search | CLaiMM standard | `claimm-mcp` |
| US datasets (raw data) | CLaiMM agnostic | `claimm-mcp-agnostic` |
| Global production stats | BGS_MCP | `bgs-mcp` |
| Both sources in one workflow | Use `claimm-mcp` + `bgs-mcp` together | Both commands |

### For Other LLMs (OpenAI, Anthropic, Google, Ollama)

| Need | Recommended | Endpoint |
|------|-------------|----------|
| Global production stats | BGS_MCP REST | `http://localhost:8000` |
| US datasets only | CLaiMM MCP tools | N/A (MCP) |
| Legacy unified endpoint (deprecated) | CMM_API REST | `http://localhost:8000` |

### For Collaborators Without LLM Keys

Use any of the LLM-agnostic options:
- `claimm-mcp-agnostic` - CLAIMM data via MCP
- `bgs-mcp` - BGS data via MCP
- `cmm-mcp` - Legacy unified MCP (deprecated)
- Any REST API - Direct HTTP access

## Installation

All projects use [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone/navigate to Data_Needs directory
cd Data_Needs

# Install each project
cd CLaiMM && uv sync && cd ..
cd BGS_MCP && uv sync && cd ..
# Optional legacy package:
cd CMM_API && uv sync && cd ..
```

## Quick Start

### Start All Services

```bash
# Terminal 1: BGS REST API
cd BGS_MCP && uv run bgs-api

# Optional legacy unified REST API (deprecated)
cd CMM_API && uv run cmm-api
```

### Test the APIs

```bash
# BGS API - top lithium producers
curl "http://localhost:8000/production/ranking?commodity=lithium%20minerals&top_n=5"

# BGS API - cobalt supply chain
curl "http://localhost:8000/production/ranking?commodity=cobalt,%20mine"
```

## Claude Desktop Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "bgs": {
      "command": "uv",
      "args": ["--directory", "/path/to/BGS_MCP", "run", "bgs-mcp"]
    },
    "claimm-agnostic": {
      "command": "uv",
      "args": ["--directory", "/path/to/CLaiMM", "run", "claimm-mcp-agnostic"],
      "env": {
        "EDX_API_KEY": "your_edx_key"
      }
    }
  }
}
```

**Recommended Setup:**
- Use `bgs` plus either `claimm-mcp` or `claimm-mcp-agnostic`
- Add legacy `cmm-mcp` only for backward compatibility

## Project Details

### CLaiMM (`CLaiMM/`)

MCP servers for NETL EDX CLAIMM (Critical Minerals and Materials) data.

**Two Variants:**

| Variant | Command | Tools | LLM Required |
|---------|---------|-------|--------------|
| Standard | `claimm-mcp` | 8 | Yes (OpenAI, Anthropic, etc.) |
| Agnostic | `claimm-mcp-agnostic` | 10 | No |

**Agnostic Tools:**
- `search_claimm_datasets` - Search by query/tags
- `get_dataset_details` - Full metadata
- `list_claimm_datasets` - List all datasets
- `search_resources` - Search files
- `get_resource_details` - File metadata
- `get_download_url` - Direct download links
- `detect_file_schema` - CSV/Excel column detection
- `detect_dataset_schemas` - Schema for all files
- `get_claimm_statistics` - Format/tag stats
- `get_datasets_by_category` - Organized by topic

**Data Categories:**
- Rare Earth Elements (75 datasets)
- Produced Water (27 datasets)
- Geology (33 datasets)
- Geochemistry (18 datasets)
- Coal & Coal Byproducts (11 datasets)
- Mine Waste (4 datasets)
- Lithium (1 dataset)

### BGS_MCP (`BGS_MCP/`)

MCP server and REST API for BGS World Mineral Statistics.

**Interfaces:**

| Interface | Command | Use Case |
|-----------|---------|----------|
| MCP Server | `bgs-mcp` | Claude Desktop/Code |
| REST API | `bgs-api` | Any LLM, HTTP clients |

**MCP Tools (8):**
- `list_commodities` - Available minerals
- `list_countries` - Countries with data
- `search_production` - Search by filters
- `get_commodity_ranking` - Top producers
- `get_time_series` - Historical trends
- `compare_countries` - Country comparison
- `get_country_profile` - Country's commodities
- `get_api_info` - Documentation

**REST Endpoints:**
- `GET /commodities` - List minerals
- `GET /countries` - List countries
- `GET /production/search` - Search data
- `GET /production/ranking` - Top producers
- `GET /production/timeseries` - Trends
- `GET /production/compare` - Compare countries
- `GET /countries/{iso}/profile` - Country profile
- `GET /openai/functions` - LLM tool definitions

**Critical Minerals (28):**
- Battery: lithium, cobalt, nickel, graphite, manganese
- Rare Earth: minerals, oxides
- Strategic: platinum, tungsten, vanadium, chromium, tantalum/niobium
- Technology: gallium, germanium, indium, beryl
- Base: copper, zinc, lead, gold, silver, antimony, molybdenum, iron

### CMM_API (`CMM_API/`, Legacy/Deprecated)

> Status: Deprecated for new usage. Retained for backward compatibility.

Unified API combining both CLAIMM and BGS data sources.

**Interfaces:**

| Interface | Command | Description |
|-----------|---------|-------------|
| MCP Server | `cmm-mcp` | Claude Desktop/Code |
| REST API | `cmm-api` | Any LLM, HTTP clients |

**MCP Tools (8):**
- `get_data_overview` - All sources overview
- `search_all_sources` - Unified search
- `list_bgs_commodities` - BGS minerals
- `search_bgs_production` - BGS data
- `get_commodity_ranking` - Top producers
- `search_claimm_datasets` - CLAIMM search
- `get_claimm_dataset` - Dataset details
- `get_claimm_categories` - CLAIMM categories

**REST Endpoints:**
- `GET /overview` - All sources overview
- `GET /search?q=` - Unified search
- `GET /bgs/commodities` - BGS minerals
- `GET /bgs/production` - BGS data
- `GET /bgs/ranking/{commodity}` - Top producers
- `GET /claimm/datasets` - CLAIMM search
- `GET /claimm/datasets/{id}` - Dataset details
- `GET /claimm/categories` - CLAIMM categories
- `GET /openai/functions` - LLM tool definitions

## LLM Integration

### OpenAI

```python
import httpx
from openai import OpenAI

API_BASE = "http://localhost:8000"  # BGS_MCP REST API
client = OpenAI()

# Get function definitions
functions = httpx.get(f"{API_BASE}/openai/functions").json()["functions"]

# Use with chat completions
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Top lithium producers?"}],
    tools=[{"type": "function", "function": f} for f in functions],
)
```

### Anthropic Claude (API)

```python
import anthropic
import httpx

API_BASE = "http://localhost:8000"  # BGS_MCP REST API
client = anthropic.Anthropic()

functions = httpx.get(f"{API_BASE}/openai/functions").json()["functions"]
tools = [{"name": f["name"], "description": f["description"],
          "input_schema": f["parameters"]} for f in functions]

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "Search for rare earth datasets"}]
)
```

### Ollama (Local LLMs)

```python
import httpx
import json

API_BASE = "http://localhost:8000"
OLLAMA_BASE = "http://localhost:11434"

# Fetch data first
data = httpx.get(f"{API_BASE}/bgs/ranking/cobalt,%20mine").json()

# Ask LLM to analyze
response = httpx.post(
    f"{OLLAMA_BASE}/api/chat",
    json={
        "model": "phi4",
        "messages": [
            {"role": "system", "content": "You are a minerals analyst."},
            {"role": "user", "content": f"Analyze: {json.dumps(data)}"}
        ],
        "stream": False
    },
    timeout=120.0
)
print(response.json()["message"]["content"])
```

### Plain HTTP

```bash
# Top cobalt producers
curl "http://localhost:8000/production/ranking?commodity=cobalt,%20mine&top_n=10"

# Country profile
curl "http://localhost:8000/countries/AU/profile"

# Commodity list
curl "http://localhost:8000/commodities?critical_only=true"
```

## Environment Variables

| Variable | Required For | Description |
|----------|--------------|-------------|
| `EDX_API_KEY` | CLAIMM access | NETL EDX API key |
| `OPENAI_API_KEY` | CLaiMM standard | OpenAI API key |
| `ANTHROPIC_API_KEY` | CLaiMM standard | Anthropic API key |
| `GOOGLE_API_KEY` | CLaiMM standard | Google AI API key |
| `XAI_API_KEY` | CLaiMM standard | xAI (Grok) API key |

**Note:** BGS data requires no API keys (open data).

## Use Cases

### Supply Chain Analysis

```bash
# Identify concentration risk
curl "http://localhost:8000/bgs/ranking/cobalt,%20mine?top_n=10"
# Result: DRC produces 69% of global cobalt

# Compare alternative sources
curl "http://localhost:8000/bgs/production?commodity=cobalt,%20mine&country=AUS"
```

### Research Data Discovery

Use `claimm-mcp` or `claimm-mcp-agnostic` tools:
- `search_claimm_datasets` to find datasets by query
- `get_dataset_details` to retrieve full metadata and download URLs

### Market Intelligence

```bash
# Production trends
curl "http://localhost:8000/production/search?commodity=lithium%20minerals&year_from=2018"

# Country mineral profile
curl "http://localhost:8000/countries/AU/profile"
```

### AI-Powered Analysis

Use with Claude Desktop:
- "What are the top rare earth producing countries and what are the supply chain risks?"
- "Find CLAIMM datasets about produced water and show their schemas"
- "Compare lithium production between Australia and Chile over the last 5 years"

## Testing

### Test Scripts Available

| Project | Test File | Description |
|---------|-----------|-------------|
| BGS_MCP | `test_openai.py` | OpenAI integration |
| BGS_MCP | `test_ollama.py` | Ollama integration |
| CMM_API (legacy) | `test_openai.py` | OpenAI integration |
| CMM_API (legacy) | `test_ollama.py` | Ollama integration |

### Run Tests

```bash
# BGS with OpenAI
cd BGS_MCP
export OPENAI_API_KEY=your_key
uv run python test_openai.py

# Legacy CMM API with Ollama
cd CMM_API
uv run python test_ollama.py
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Applications                      │
├─────────────────────────────────────────────────────────────┤
│  Claude Desktop  │  Claude Code  │  OpenAI  │  Ollama  │ ... │
└────────┬─────────┴───────┬───────┴────┬─────┴────┬─────┴─────┘
         │                 │            │          │
         │ MCP             │ MCP        │ HTTP     │ HTTP
         ▼                 ▼            ▼          ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│   CLaiMM MCP    │ │   BGS MCP       │ │   REST APIs         │
│   (standard/    │ │   Server        │ │   (BGS primary,     │
│    agnostic)    │ │                 │ │    CMM legacy)      │
└────────┬────────┘ └────────┬────────┘ └──────────┬──────────┘
         │                   │                     │
         ▼                   ▼                     ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│   EDX Client    │ │   BGS Client    │ │   Legacy Unified    │
│                 │ │                 │ │   Client (optional) │
└────────┬────────┘ └────────┬────────┘ └──────────┬──────────┘
         │                   │                     │
         ▼                   ▼                     ▼
┌─────────────────┐ ┌─────────────────┐
│  NETL EDX API   │ │  BGS OGC API    │
│  (CKAN-based)   │ │  (OGC Features) │
└─────────────────┘ └─────────────────┘
```

## Data Licenses

| Source | License | URL |
|--------|---------|-----|
| CLAIMM (NETL EDX) | US Government Work | https://edx.netl.doe.gov |
| BGS World Mineral Statistics | Open Government Licence | https://www.bgs.ac.uk |

## Contributing

Each project accepts contributions. Please ensure:
- Code maintains LLM-agnostic patterns where applicable
- REST APIs include OpenAI function definitions
- MCP servers follow FastMCP patterns
- Documentation is updated

## License

All projects are MIT licensed.
