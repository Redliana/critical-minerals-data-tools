# CMM API - Unified Critical Minerals and Materials API

> **DEPRECATED**: This REST API is deprecated in favor of the dedicated MCP servers
> which provide fuller coverage and direct LLM integration:
>
> - **CLaiMM MCP Server** (`Data_Needs/CLaiMM_MCP/`) - 17 tools for NETL EDX CLAIMM data
> - **BGS MCP Server** (`Data_Needs/BGS_MCP/`) - 11 tools for BGS World Mineral Statistics
>
> Together these MCP servers expose 28 tools (vs 7 endpoints here) and integrate
> directly with Claude Code and Claude Desktop without needing a running REST server.
>
> This package is kept for reference only and may be removed in a future cleanup.

---

A unified REST API that combines multiple critical minerals data sources into a single, LLM-friendly interface. Designed for supply chain analysis, research, and AI-powered applications.

## Overview

CMM API aggregates data from two authoritative sources:

| Source | Description | Data Types | Coverage |
|--------|-------------|------------|----------|
| **CLAIMM (NETL EDX)** | US Critical Minerals and Materials datasets | Datasets, CSV files, schemas, research data | US-focused, 200+ datasets |
| **BGS World Mineral Statistics** | Global mineral production and trade statistics | Production, imports, exports | Global, 1970-2023 |

### Key Features

- **Unified Search**: Query both data sources with a single API call
- **LLM Integration**: OpenAI-compatible function definitions for AI agents
- **Production Rankings**: Get top producing countries for any commodity
- **Dataset Discovery**: Search and browse CLAIMM datasets with download URLs
- **Supply Chain Analysis**: Compare countries, track trends, identify risks

## Installation

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Setup

```bash
# Clone or navigate to the project directory
cd CMM_API

# Install dependencies with uv
uv sync

# Or with pip
pip install -e .
```

### Environment Variables (Optional)

Create a `.env` file for configuration:

```bash
# NETL EDX API key (optional, for authenticated access)
EDX_API_KEY=your_edx_api_key

# Server configuration
API_HOST=0.0.0.0
API_PORT=8000
```

## Quick Start

### Start the Server

```bash
# With uv
uv run cmm-api

# Or directly with uvicorn
uv run uvicorn cmm_api.server:app --host 127.0.0.1 --port 8000
```

The API will be available at `http://127.0.0.1:8000`

### Basic Usage

```bash
# Get API overview
curl http://127.0.0.1:8000/

# Search across all sources
curl "http://127.0.0.1:8000/search?q=lithium"

# Get top lithium producers
curl "http://127.0.0.1:8000/bgs/ranking/lithium%20minerals?top_n=10"

# Search CLAIMM datasets
curl "http://127.0.0.1:8000/claimm/datasets?q=rare%20earth"
```

## API Reference

### Root Endpoints

#### `GET /`
Returns API information and available endpoints.

#### `GET /overview`
Returns comprehensive overview of all data sources, including:
- CLAIMM dataset categories and counts
- BGS available commodities
- Data type descriptions and time ranges

**Example Response:**
```json
{
  "sources": {
    "CLAIMM": {
      "name": "NETL EDX CLAIMM",
      "description": "US Critical Minerals and Materials datasets",
      "categories": {
        "Rare Earth Elements": 75,
        "Coal & Coal Byproducts": 11,
        "Produced Water": 27,
        "Geology": 33,
        "Geochemistry": 18
      }
    },
    "BGS": {
      "name": "BGS World Mineral Statistics",
      "description": "Global mineral production and trade statistics",
      "time_range": "1970-2023",
      "commodities": ["lithium minerals", "cobalt, mine", "..."]
    }
  }
}
```

### Unified Search

#### `GET /search`
Search across all data sources simultaneously.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | required | Search query |
| `sources` | string | "CLAIMM,BGS" | Comma-separated sources to search |
| `limit` | int | 20 | Maximum results per source |

**Example:**
```bash
curl "http://127.0.0.1:8000/search?q=cobalt&sources=CLAIMM,BGS&limit=10"
```

### BGS Endpoints

#### `GET /bgs/commodities`
List available BGS commodities.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `critical_only` | bool | false | Only return critical minerals |

**Available Critical Minerals:**
- lithium minerals
- cobalt, mine / cobalt, refined
- nickel, mine / nickel, smelter/refinery
- graphite
- manganese ore
- rare earth minerals / rare earth oxides
- platinum group metals, mine
- vanadium, mine
- tungsten, mine
- chromium ores and concentrates
- tantalum and niobium minerals
- titanium minerals
- gallium, primary
- germanium metal
- indium, refinery
- copper, mine / copper, refined
- zinc, mine / lead, mine
- gold, mine / silver, mine
- antimony, mine
- molybdenum, mine
- iron ore

#### `GET /bgs/production`
Search BGS production data.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `commodity` | string | null | Commodity name (e.g., "lithium minerals") |
| `country` | string | null | Country name or ISO3 code |
| `year_from` | int | null | Start year filter |
| `year_to` | int | null | End year filter |
| `statistic_type` | string | "Production" | Production, Imports, or Exports |
| `limit` | int | 100 | Maximum records to return |

**Example:**
```bash
# Get Australian lithium production
curl "http://127.0.0.1:8000/bgs/production?commodity=lithium%20minerals&country=AUS"

# Get cobalt imports to China
curl "http://127.0.0.1:8000/bgs/production?commodity=cobalt,%20mine&country=CHN&statistic_type=Imports"
```

#### `GET /bgs/ranking/{commodity}`
Get top producing countries for a commodity.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `commodity` | path | required | Commodity name |
| `year` | int | null | Year (defaults to most recent) |
| `top_n` | int | 15 | Number of top countries |

**Example Response:**
```json
{
  "commodity": "lithium minerals",
  "year": 2023,
  "ranking": [
    {
      "country": "Australia",
      "country_iso": "AUS",
      "quantity": 3386775.0,
      "units": "tonnes (metric)",
      "rank": 1,
      "share_percent": 65.38
    },
    {
      "country": "Zimbabwe",
      "country_iso": "ZWE",
      "quantity": 788785.0,
      "units": "tonnes (metric)",
      "rank": 2,
      "share_percent": 15.23
    }
  ]
}
```

### CLAIMM Endpoints

#### `GET /claimm/datasets`
Search CLAIMM datasets.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | null | Search query |
| `tags` | string | null | Comma-separated tags to filter |
| `limit` | int | 20 | Maximum datasets to return |

**Example:**
```bash
curl "http://127.0.0.1:8000/claimm/datasets?q=produced%20water&limit=5"
```

**Example Response:**
```json
{
  "count": 5,
  "datasets": [
    {
      "source": "CLAIMM",
      "id": "e564c03f-d309-4b2f-8972-ff0a4212b5b8",
      "title": "Pennsylvania DEP Produced Water Compositions",
      "description": "Database of geochemical compositions...",
      "tags": ["Critical Minerals", "Produced water"],
      "resources": [
        {
          "id": "8dc8eb43-2375-4908-a3e4-3b02931a42be",
          "name": "PA_OLI_processed.xlsx",
          "format": "XLSX",
          "size": 217188,
          "url": "https://edx.netl.doe.gov/resource/8dc8eb43-2375-4908-a3e4-3b02931a42be/download"
        }
      ]
    }
  ]
}
```

#### `GET /claimm/datasets/{dataset_id}`
Get detailed information about a specific dataset.

#### `GET /claimm/categories`
Get dataset categories and counts.

**Example Response:**
```json
{
  "Rare Earth Elements": 75,
  "Coal & Coal Byproducts": 11,
  "Produced Water": 27,
  "Geology": 33,
  "Geochemistry": 18,
  "Mine Waste": 4,
  "Lithium": 1,
  "Other": 31
}
```

### LLM Integration

#### `GET /openai/functions`
Returns OpenAI-compatible function definitions for all API endpoints.

Use these definitions with OpenAI's function calling, or adapt them for other LLM providers.

**Available Functions:**
| Function | Description |
|----------|-------------|
| `search_all_sources` | Search across all data sources |
| `get_bgs_production` | Search BGS production data |
| `get_commodity_ranking` | Get top producing countries |
| `search_claimm_datasets` | Search CLAIMM datasets |
| `get_claimm_dataset_details` | Get dataset details |
| `list_bgs_commodities` | List available commodities |
| `get_data_overview` | Get overview of all sources |

## LLM Integration Examples

### OpenAI (GPT-4)

```python
import json
import httpx
from openai import OpenAI

API_BASE = "http://127.0.0.1:8000"
client = OpenAI()

# Fetch function definitions
functions = httpx.get(f"{API_BASE}/openai/functions").json()["functions"]

# Create chat completion with tools
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Who are the top cobalt producers?"}],
    tools=[{"type": "function", "function": f} for f in functions],
)

# Handle tool calls
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    func_name = tool_call.function.name
    func_args = json.loads(tool_call.function.arguments)

    # Map function to endpoint and call API
    result = httpx.get(f"{API_BASE}/bgs/ranking/{func_args['commodity']}").json()
```

See `test_openai.py` for a complete working example.

### Ollama (Local LLMs)

For local LLMs that don't support function calling, use the simple query approach:

```python
import json
import httpx

API_BASE = "http://127.0.0.1:8000"
OLLAMA_BASE = "http://127.0.0.1:11434"

# Fetch data first
data = httpx.get(f"{API_BASE}/bgs/ranking/lithium minerals").json()

# Ask LLM to analyze
response = httpx.post(
    f"{OLLAMA_BASE}/api/chat",
    json={
        "model": "phi4",
        "messages": [
            {"role": "system", "content": "You are a minerals analyst."},
            {"role": "user", "content": f"Analyze this data: {json.dumps(data)}"}
        ],
        "stream": False
    }
)
print(response.json()["message"]["content"])
```

See `test_ollama.py` for a complete working example.

### Claude (Anthropic)

```python
import anthropic
import httpx
import json

API_BASE = "http://127.0.0.1:8000"
client = anthropic.Anthropic()

# Fetch and convert function definitions to Claude format
functions = httpx.get(f"{API_BASE}/openai/functions").json()["functions"]
tools = [
    {
        "name": f["name"],
        "description": f["description"],
        "input_schema": f["parameters"]
    }
    for f in functions
]

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "What rare earth datasets are available?"}]
)
```

## Project Structure

```
CMM_API/
├── pyproject.toml          # Project configuration and dependencies
├── README.md               # This file
├── test_openai.py          # OpenAI integration test
├── test_ollama.py          # Ollama integration test
└── src/
    └── cmm_api/
        ├── __init__.py     # Package initialization
        ├── config.py       # Configuration settings
        ├── clients.py      # Data clients (BGS, CLAIMM, Unified)
        └── server.py       # FastAPI REST API server
```

## Data Sources

### CLAIMM (NETL EDX)

**URL:** https://edx.netl.doe.gov/edxapps/claimm/

CLAIMM (Critical Minerals and Materials) is a centralized data platform from the National Energy Technology Laboratory (NETL) that provides access to US critical minerals datasets, including:

- Rare Earth Elements in coal and coal byproducts
- Produced water geochemistry
- Mine waste characterization
- Geological surveys and data
- Research publications and supplementary data

### BGS World Mineral Statistics

**URL:** https://www.bgs.ac.uk/mineralsuk/statistics/world-mineral-statistics/

The British Geological Survey provides comprehensive global mineral statistics covering:

- Production data by country (1970-2023)
- Import/export statistics
- 100+ mineral commodities
- Annual updates

**API:** OGC Features API at https://ogcapi.bgs.ac.uk/collections/world-mineral-statistics

## Use Cases

### Supply Chain Analysis
```bash
# Identify top producers and concentration risk
curl "http://127.0.0.1:8000/bgs/ranking/cobalt,%20mine?top_n=10"

# Track production trends
curl "http://127.0.0.1:8000/bgs/production?commodity=lithium%20minerals&year_from=2018&year_to=2023"
```

### Research Data Discovery
```bash
# Find datasets on specific topics
curl "http://127.0.0.1:8000/claimm/datasets?q=produced%20water%20lithium"

# Get dataset details with download URLs
curl "http://127.0.0.1:8000/claimm/datasets/e564c03f-d309-4b2f-8972-ff0a4212b5b8"
```

### AI-Powered Analysis
```bash
# Get function definitions for LLM integration
curl "http://127.0.0.1:8000/openai/functions"

# Unified search for comprehensive results
curl "http://127.0.0.1:8000/search?q=rare%20earth%20production"
```

## Testing

### Run OpenAI Integration Test

```bash
export OPENAI_API_KEY=your_key_here
uv run python test_openai.py
```

### Run Ollama Integration Test

```bash
# Ensure Ollama is running with a model (e.g., phi4)
ollama run phi4

# In another terminal
uv run python test_ollama.py
```

## Dependencies

- **fastapi** - REST API framework
- **uvicorn** - ASGI server
- **httpx** - Async HTTP client
- **pydantic** - Data validation
- **pydantic-settings** - Configuration management
- **python-dotenv** - Environment variable loading
- **openai** - OpenAI API client (for testing)

## License

This project is for research and educational purposes. Data from CLAIMM and BGS is subject to their respective terms of use.

## Related Projects

- **CLaiMM MCP Server** - MCP server for CLAIMM with LLM support
- **BGS MCP Server** - MCP server for BGS World Mineral Statistics

## Contributing

Contributions are welcome! Please ensure any changes maintain compatibility with both data sources and LLM integration patterns.
