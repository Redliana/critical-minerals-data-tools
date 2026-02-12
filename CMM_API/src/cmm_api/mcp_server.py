"""MCP Server for Unified Critical Minerals and Materials API."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .clients import BGSClient, CLAIMMClient, UnifiedClient

# Initialize MCP server
mcp = FastMCP(
    "CMM",
    instructions="""Unified Critical Minerals and Materials data server.

Provides access to two data sources:
- CLAIMM (NETL EDX): US Critical Minerals datasets, schemas, research data
- BGS World Mineral Statistics: Global production/trade data (1970-2023)

Use these tools for supply chain analysis, research data discovery, and mineral market insights.""",
)

# Initialize clients
bgs = BGSClient()
claimm = CLAIMMClient()
unified = UnifiedClient()


# ============================================================================
# Overview Tools
# ============================================================================


@mcp.tool()
async def get_data_overview() -> dict:
    """Get overview of all available data sources.

    Returns information about CLAIMM and BGS data sources including:
    - Available categories and dataset counts
    - List of commodities
    - Data types and time ranges
    """
    return await unified.get_overview()


@mcp.tool()
async def search_all_sources(
    query: str,
    sources: str = "CLAIMM,BGS",
    limit: int = 20,
) -> dict:
    """Search across all critical minerals data sources.

    Args:
        query: Search query (e.g., "lithium", "rare earth", "cobalt production")
        sources: Comma-separated sources to search (CLAIMM,BGS)
        limit: Maximum results per source

    Returns results from both CLAIMM datasets and BGS production data.
    """
    source_list = [s.strip().upper() for s in sources.split(",")]
    return await unified.search_all(query=query, sources=source_list, limit=limit)


# ============================================================================
# BGS Tools
# ============================================================================


@mcp.tool()
async def list_bgs_commodities(critical_only: bool = False) -> list[str]:
    """List available commodities in BGS World Mineral Statistics.

    Args:
        critical_only: If True, only return critical minerals list

    Returns list of commodity names that can be used with other BGS tools.
    """
    return await bgs.get_commodities(critical_only=critical_only)


@mcp.tool()
async def search_bgs_production(
    commodity: str | None = None,
    country: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    statistic_type: str = "Production",
    limit: int = 100,
) -> dict:
    """Search BGS World Mineral Statistics production data.

    Args:
        commodity: Commodity name (e.g., "lithium minerals", "cobalt, mine")
        country: Country name or ISO3 code (e.g., "Australia" or "AUS")
        year_from: Start year filter
        year_to: End year filter
        statistic_type: "Production", "Imports", or "Exports"
        limit: Maximum records to return

    Returns production/trade records with quantity, units, and country info.
    """
    records = await bgs.search_production(
        commodity=commodity,
        country=country,
        year_from=year_from,
        year_to=year_to,
        statistic_type=statistic_type,
        limit=limit,
    )
    return {
        "count": len(records),
        "records": [r.model_dump() for r in records],
    }


@mcp.tool()
async def get_commodity_ranking(
    commodity: str,
    year: int | None = None,
    top_n: int = 15,
) -> dict:
    """Get top producing countries for a mineral commodity.

    Args:
        commodity: Commodity name (e.g., "lithium minerals", "cobalt, mine", "rare earth minerals")
        year: Year for ranking (defaults to most recent available)
        top_n: Number of top countries to return

    Returns ranked list with quantities, market shares, and country info.
    Useful for supply chain analysis and identifying concentration risks.
    """
    ranking = await bgs.get_ranking(commodity=commodity, year=year, top_n=top_n)
    return {
        "commodity": commodity,
        "year": ranking[0]["year"] if ranking else None,
        "ranking": ranking,
    }


# ============================================================================
# CLAIMM Tools
# ============================================================================


@mcp.tool()
async def search_claimm_datasets(
    query: str | None = None,
    tags: str | None = None,
    limit: int = 20,
) -> dict:
    """Search CLAIMM datasets from NETL EDX.

    Args:
        query: Search query (e.g., "rare earth", "produced water", "coal ash")
        tags: Comma-separated tags to filter
        limit: Maximum datasets to return

    Returns datasets with titles, descriptions, tags, and download URLs.
    """
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    datasets = await claimm.search_datasets(query=query, tags=tag_list, limit=limit)
    return {
        "count": len(datasets),
        "datasets": [ds.model_dump() for ds in datasets],
    }


@mcp.tool()
async def get_claimm_dataset(dataset_id: str) -> dict | None:
    """Get detailed information about a specific CLAIMM dataset.

    Args:
        dataset_id: Dataset ID from search results

    Returns full dataset metadata including all resources with download URLs.
    """
    dataset = await claimm.get_dataset(dataset_id)
    return dataset.model_dump() if dataset else None


@mcp.tool()
async def get_claimm_categories() -> dict[str, int]:
    """Get CLAIMM dataset categories and counts.

    Returns dictionary of category names and number of datasets in each.
    Categories include: Rare Earth Elements, Coal & Coal Byproducts,
    Produced Water, Geology, Geochemistry, Mine Waste, Lithium, etc.
    """
    return await claimm.get_categories()


# ============================================================================
# Entry Point
# ============================================================================


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
