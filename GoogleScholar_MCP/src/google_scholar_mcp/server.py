"""Google Scholar MCP server."""

from __future__ import annotations

import logging

from cmm_data.clients import GoogleScholarClient
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("google-scholar-mcp")

mcp = FastMCP(
    "google-scholar",
    instructions=(
        "Search Google Scholar for peer-reviewed papers, conference proceedings, and preprints."
    ),
)


@mcp.tool()
def search_scholar(
    query: str,
    year_from: int | None = None,
    year_to: int | None = None,
    num_results: int = 10,
) -> dict:
    """
    Search Google Scholar and return normalized paper metadata.

    Args:
        query: Query string.
        year_from: Optional lower year bound.
        year_to: Optional upper year bound.
        num_results: Maximum papers to return (1-20).

    Returns:
        Dictionary payload with `query`, `total_results`, `papers`, and optional `error`.
    """
    client = GoogleScholarClient()
    result = client.search_scholar(
        query=query,
        year_from=year_from,
        year_to=year_to,
        num_results=num_results,
    )
    return result.to_dict()


def main() -> None:
    """Run stdio MCP server."""
    logger.info("Starting Google Scholar MCP server")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
