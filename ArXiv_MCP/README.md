# ArXiv MCP Server with LLM Integration

A Model Context Protocol (MCP) server that enables AI applications to search ArXiv papers and generate summaries using commercial LLMs (OpenAI GPT, Anthropic Claude).

## Features

- **Search ArXiv**: Query the ArXiv repository for academic papers
- **Get Paper Details**: Retrieve full metadata for specific papers
- **LLM Summarization**: Generate concise summaries using GPT or Claude
- **Batch Processing**: Search and summarize multiple papers at once

## Quick Start

### Prerequisites

- Python 3.10 or higher
- API key for OpenAI or Anthropic (optional, for summarization features)

### Installation

1. Clone or download this repository
2. Run the setup script:

```bash
./setup.sh
```

3. Activate the virtual environment:

```bash
source venv/bin/activate
```

4. Set your API keys (optional, for LLM features):

```bash
export OPENAI_API_KEY='your-openai-api-key'
export ANTHROPIC_API_KEY='your-anthropic-api-key'
```

### Testing the Server

Test the server locally using the test client:

```bash
python test_client.py
```

Or use the MCP Inspector:

```bash
mcp dev src/arxiv_mcp/server.py
```

## Configuration

### Claude Desktop

To use this server with Claude Desktop, add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "arxiv-search": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/ArXiv_MCP",
        "run",
        "arxiv-mcp"
      ],
      "env": {
        "OPENAI_API_KEY": "your-key-here",
        "ANTHROPIC_API_KEY": "your-key-here"
      }
    }
  }
}
```

Location of config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

## Available Tools

### 1. search_arxiv

Search ArXiv for papers matching a query.

**Parameters:**
- `query` (string): Search query (supports field prefixes like `ti:`, `au:`, `abs:`)
- `max_results` (int): Maximum results to return (default: 10, max: 100)
- `sort_by` (string): Sort order - "relevance", "lastUpdatedDate", or "submittedDate"

**Example:**
```
search_arxiv(query="machine learning", max_results=5)
```

### 2. get_arxiv_paper

Get detailed information about a specific paper by ArXiv ID.

**Parameters:**
- `arxiv_id` (string): The ArXiv ID (e.g., "2301.07041")

**Example:**
```
get_arxiv_paper(arxiv_id="1706.03762")
```

### 3. summarize_paper_with_llm

Fetch a paper and generate a summary using an LLM.

**Parameters:**
- `arxiv_id` (string): The ArXiv ID to summarize
- `llm_provider` (string): "openai" or "anthropic" (default: "openai")
- `model` (string): Specific model or "auto" for default

**Example:**
```
summarize_paper_with_llm(arxiv_id="1706.03762", llm_provider="openai")
```

### 4. search_and_summarize

Search ArXiv and automatically summarize the top papers.

**Parameters:**
- `query` (string): Search query
- `max_papers` (int): Number of papers to summarize (default: 3, max: 5)
- `llm_provider` (string): "openai" or "anthropic"

**Example:**
```
search_and_summarize(query="transformer attention", max_papers=3)
```

## Implementation Variants

This tutorial includes two implementations:

1. **src/arxiv_mcp/server.py**: Direct API calls using `httpx`
2. **src/arxiv_mcp/server_sdk.py**: Using official OpenAI and Anthropic SDKs

Both implementations provide the same functionality. The SDK version offers better error handling and type safety.

## Architecture

The server follows the MCP architecture:

```
AI Application (MCP Host)
    ↓
MCP Client
    ↓ (JSON-RPC 2.0 via STDIO)
MCP Server (this application)
    ↓
ArXiv API + Commercial LLM APIs
```

## ArXiv API Search Syntax

The ArXiv API supports field-specific searches:

- `ti:` - Title
- `au:` - Author
- `abs:` - Abstract
- `cat:` - Category
- `all:` - All fields

**Boolean operators:**
- `AND` - Both terms must appear
- `OR` - Either term must appear
- `ANDNOT` - First term without second

**Examples:**
- `ti:transformer AND au:vaswani`
- `cat:cs.AI AND abs:reinforcement learning`
- `all:quantum computing`

## Known Issues and Fixes

### ArXiv API HTTPS Redirect (Fixed)

The ArXiv API now requires HTTPS. The server uses `https://export.arxiv.org/api/query` to avoid 301 redirects that can cause failures with some HTTP clients.

### Test Client Environment Variables (Fixed)

The test client passes environment variables to the subprocess so that API keys are available to the server:

```python
server_params = StdioServerParameters(
    command="uv",
    args=["run", "arxiv-mcp"],
    env=os.environ.copy()  # Required for API keys
)
```

## Troubleshooting

### Server not appearing in Claude Desktop

1. Check the config file path is correct
2. Verify the absolute path to the `ArXiv_MCP` directory is correct
3. Restart Claude Desktop after editing config
4. Check Claude Desktop logs for errors

### LLM summarization not working

1. Verify API keys are set correctly
2. Check API key has sufficient credits/quota
3. Review server logs for API errors
4. Test API keys with a simple curl command

### ArXiv API errors

1. Check internet connection
2. Verify ArXiv API is not rate-limiting (wait 3 seconds between requests)
3. Simplify search query if getting no results

## License

MIT License - see tutorial documentation for details.

## Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [ArXiv API User Manual](https://info.arxiv.org/help/api/user-manual.html)
- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [Anthropic API Documentation](https://docs.anthropic.com/)
