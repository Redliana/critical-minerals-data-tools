"""Provider-agnostic and provider-specific tool schemas for Google Scholar."""

from __future__ import annotations

from typing import Any

from cmm_data.clients import GoogleScholarClient

TOOL_SCHEMA = {
    "name": "search_scholar",
    "description": "Search Google Scholar for papers, proceedings, and preprints.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query string"},
            "year_from": {"type": "integer", "description": "Lower publication year bound"},
            "year_to": {"type": "integer", "description": "Upper publication year bound"},
            "num_results": {
                "type": "integer",
                "description": "Maximum number of results (1-20)",
                "default": 10,
            },
        },
        "required": ["query"],
    },
}


def get_tool_schema() -> dict[str, Any]:
    """Return provider-agnostic schema."""
    return TOOL_SCHEMA.copy()


def get_openai_tools() -> list[dict[str, Any]]:
    """Return OpenAI function-calling tool definition."""
    return [{"type": "function", "function": TOOL_SCHEMA.copy()}]


def get_anthropic_tools() -> list[dict[str, Any]]:
    """Return Anthropic tool definition."""
    return [
        {
            "name": TOOL_SCHEMA["name"],
            "description": TOOL_SCHEMA["description"],
            "input_schema": TOOL_SCHEMA["parameters"],
        }
    ]


def execute_search(arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute `search_scholar` with provided arguments."""
    client = GoogleScholarClient()
    result = client.search_scholar(**arguments)
    return result.to_dict()
