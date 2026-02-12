"""Unified REST API server for Critical Minerals and Materials data.

.. deprecated::
    This REST API is deprecated. Use the dedicated MCP servers instead:
    - CLaiMM_MCP (Data_Needs/CLaiMM_MCP/) - 17 tools for NETL EDX CLAIMM data
    - BGS_MCP (Data_Needs/BGS_MCP/) - 11 tools for BGS World Mineral Statistics
    These provide fuller coverage (28 vs 7 endpoints) and direct LLM integration.
"""

import warnings

warnings.warn(
    "CMM_API is deprecated. Use CLaiMM_MCP and BGS_MCP servers instead, "
    "which provide 28 tools (vs 7 endpoints here) with direct LLM integration. "
    "See Data_Needs/CLaiMM_MCP/ and Data_Needs/BGS_MCP/.",
    DeprecationWarning,
    stacklevel=2,
)

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .clients import BGSClient, CLAIMMClient, UnifiedClient

app = FastAPI(
    title="CMM API",
    description="Unified REST API for Critical Minerals and Materials - Combines CLAIMM (NETL EDX) and BGS World Mineral Statistics",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
bgs_client = BGSClient()
claimm_client = CLAIMMClient()
unified_client = UnifiedClient()


# ============================================================================
# Root & Overview
# ============================================================================

@app.get("/")
async def root():
    """API information and available endpoints."""
    return {
        "name": "CMM API",
        "version": "0.1.0",
        "description": "Unified Critical Minerals and Materials API",
        "sources": ["CLAIMM (NETL EDX)", "BGS World Mineral Statistics"],
        "endpoints": {
            "overview": "/overview",
            "search": "/search?q=<query>",
            "bgs": {
                "commodities": "/bgs/commodities",
                "production": "/bgs/production",
                "ranking": "/bgs/ranking/{commodity}",
            },
            "claimm": {
                "datasets": "/claimm/datasets",
                "dataset": "/claimm/datasets/{id}",
                "categories": "/claimm/categories",
            },
            "openai": "/openai/functions",
        },
    }


@app.get("/overview")
async def get_overview():
    """Get overview of all data sources."""
    return await unified_client.get_overview()


# ============================================================================
# Unified Search
# ============================================================================

@app.get("/search")
async def search_all(
    q: str = Query(..., description="Search query"),
    sources: str = Query("CLAIMM,BGS", description="Comma-separated sources"),
    limit: int = Query(20, ge=1, le=100),
):
    """Search across all data sources."""
    source_list = [s.strip().upper() for s in sources.split(",")]
    return await unified_client.search_all(query=q, sources=source_list, limit=limit)


# ============================================================================
# BGS Endpoints
# ============================================================================

@app.get("/bgs/commodities")
async def get_bgs_commodities(
    critical_only: bool = Query(False, description="Only return critical minerals"),
):
    """Get list of BGS commodities."""
    return {"commodities": await bgs_client.get_commodities(critical_only=critical_only)}


@app.get("/bgs/production")
async def search_bgs_production(
    commodity: str | None = Query(None, description="Commodity name"),
    country: str | None = Query(None, description="Country name or ISO code"),
    year_from: int | None = Query(None, description="Start year"),
    year_to: int | None = Query(None, description="End year"),
    statistic_type: str = Query("Production", description="Production, Imports, or Exports"),
    limit: int = Query(100, ge=1, le=1000),
):
    """Search BGS production data."""
    records = await bgs_client.search_production(
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


@app.get("/bgs/ranking/{commodity}")
async def get_bgs_ranking(
    commodity: str,
    year: int | None = Query(None, description="Year (defaults to most recent)"),
    top_n: int = Query(15, ge=1, le=50),
):
    """Get top producing countries for a commodity."""
    ranking = await bgs_client.get_ranking(commodity=commodity, year=year, top_n=top_n)
    if not ranking:
        raise HTTPException(status_code=404, detail=f"No data found for {commodity}")
    return {
        "commodity": commodity,
        "year": ranking[0]["year"] if ranking else None,
        "ranking": ranking,
    }


# ============================================================================
# CLAIMM Endpoints
# ============================================================================

@app.get("/claimm/datasets")
async def search_claimm_datasets(
    q: str | None = Query(None, description="Search query"),
    tags: str | None = Query(None, description="Comma-separated tags"),
    limit: int = Query(20, ge=1, le=100),
):
    """Search CLAIMM datasets."""
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    datasets = await claimm_client.search_datasets(query=q, tags=tag_list, limit=limit)
    return {
        "count": len(datasets),
        "datasets": [ds.model_dump() for ds in datasets],
    }


@app.get("/claimm/datasets/{dataset_id}")
async def get_claimm_dataset(dataset_id: str):
    """Get CLAIMM dataset details."""
    dataset = await claimm_client.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
    return dataset.model_dump()


@app.get("/claimm/categories")
async def get_claimm_categories():
    """Get CLAIMM dataset categories and counts."""
    return await claimm_client.get_categories()


# ============================================================================
# OpenAI Function Definitions
# ============================================================================

@app.get("/openai/functions")
async def get_openai_functions():
    """Get OpenAI-compatible function definitions for all endpoints."""
    return {
        "functions": [
            {
                "name": "search_all_sources",
                "description": "Search across all critical minerals data sources (CLAIMM and BGS)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query (e.g., 'lithium', 'cobalt production')"},
                        "sources": {"type": "string", "description": "Comma-separated sources: CLAIMM,BGS", "default": "CLAIMM,BGS"},
                        "limit": {"type": "integer", "description": "Max results per source", "default": 20},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "get_bgs_production",
                "description": "Search BGS World Mineral Statistics production data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "commodity": {"type": "string", "description": "Commodity (e.g., 'lithium minerals', 'cobalt, mine')"},
                        "country": {"type": "string", "description": "Country name or ISO3 code"},
                        "year_from": {"type": "integer", "description": "Start year"},
                        "year_to": {"type": "integer", "description": "End year"},
                        "statistic_type": {"type": "string", "enum": ["Production", "Imports", "Exports"], "default": "Production"},
                        "limit": {"type": "integer", "default": 100},
                    },
                },
            },
            {
                "name": "get_commodity_ranking",
                "description": "Get top producing countries for a mineral commodity",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "commodity": {"type": "string", "description": "Commodity name (e.g., 'lithium minerals', 'cobalt, mine')"},
                        "year": {"type": "integer", "description": "Year (defaults to most recent)"},
                        "top_n": {"type": "integer", "description": "Number of top countries", "default": 15},
                    },
                    "required": ["commodity"],
                },
            },
            {
                "name": "search_claimm_datasets",
                "description": "Search NETL EDX CLAIMM datasets for US critical minerals data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "tags": {"type": "string", "description": "Comma-separated tags to filter"},
                        "limit": {"type": "integer", "default": 20},
                    },
                },
            },
            {
                "name": "get_claimm_dataset_details",
                "description": "Get detailed information about a specific CLAIMM dataset",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dataset_id": {"type": "string", "description": "Dataset ID"},
                    },
                    "required": ["dataset_id"],
                },
            },
            {
                "name": "list_bgs_commodities",
                "description": "List available commodities in BGS World Mineral Statistics",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "critical_only": {"type": "boolean", "description": "Only return critical minerals", "default": False},
                    },
                },
            },
            {
                "name": "get_data_overview",
                "description": "Get overview of all available data sources and their contents",
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
        ]
    }


# ============================================================================
# Entry Point
# ============================================================================

def main():
    """Run the server."""
    from .config import get_settings
    settings = get_settings()
    uvicorn.run(
        "cmm_api.server:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )


if __name__ == "__main__":
    main()
