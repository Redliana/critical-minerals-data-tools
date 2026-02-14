"""Data clients for CLAIMM (EDX) and BGS APIs."""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel

from cmm_data.clients import BGSClient as CoreBGSClient
from cmm_data.clients import CLAIMMClient as CoreCLAIMMClient

from .config import get_settings

# ============================================================================
# Shared Models
# ============================================================================


class MineralRecord(BaseModel):
    """Unified mineral data record."""

    source: str  # "CLAIMM" or "BGS"
    commodity: str
    country: str | None = None
    country_iso: str | None = None
    year: int | None = None
    quantity: float | None = None
    units: str | None = None
    statistic_type: str | None = None  # Production, Imports, Exports
    notes: str | None = None


class DatasetInfo(BaseModel):
    """Dataset metadata."""

    source: str
    id: str
    title: str
    description: str | None = None
    tags: list[str] = []
    resources: list[dict] = []


# ============================================================================
# BGS Client
# ============================================================================


class BGSClient:
    """Client for BGS World Mineral Statistics API."""

    CRITICAL_MINERALS = [
        "lithium minerals",
        "cobalt, mine",
        "cobalt, refined",
        "nickel, mine",
        "nickel, smelter/refinery",
        "graphite",
        "manganese ore",
        "rare earth minerals",
        "rare earth oxides",
        "platinum group metals, mine",
        "vanadium, mine",
        "tungsten, mine",
        "chromium ores and concentrates",
        "tantalum and niobium minerals",
        "titanium minerals",
        "gallium, primary",
        "germanium metal",
        "indium, refinery",
        "beryl",
        "copper, mine",
        "copper, refined",
        "zinc, mine",
        "lead, mine",
        "gold, mine",
        "silver, mine",
        "antimony, mine",
        "molybdenum, mine",
        "iron ore",
    ]

    def __init__(self):
        settings = get_settings()
        self._core = CoreBGSClient(base_url=settings.bgs_base_url, timeout=60.0)

    async def search_production(
        self,
        commodity: str | None = None,
        country: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        statistic_type: str = "Production",
        limit: int = 100,
    ) -> list[MineralRecord]:
        """Search BGS production data."""
        core_records = await self._core.search_production(
            commodity=commodity,
            country=country if (country and len(country) > 3) else None,
            country_iso=country if (country and len(country) <= 3) else None,
            year_from=year_from,
            year_to=year_to,
            statistic_type=statistic_type,
            limit=limit,
        )
        return [
            MineralRecord(
                source="BGS",
                commodity=r.commodity,
                country=r.country,
                country_iso=r.country_iso3,
                year=r.year,
                quantity=r.quantity,
                units=r.units,
                statistic_type=r.statistic_type,
                notes=r.notes,
            )
            for r in core_records
        ]

    async def get_commodities(self, critical_only: bool = False) -> list[str]:
        """Get list of BGS commodities."""
        if critical_only:
            return self.CRITICAL_MINERALS.copy()
        return await self._core.get_commodities()

    async def get_ranking(
        self,
        commodity: str,
        year: int | None = None,
        top_n: int = 15,
    ) -> list[dict]:
        """Get top countries for a commodity."""
        records = await self.search_production(commodity=commodity, limit=5000)

        if not records:
            return []

        # Find target year
        if year is None:
            year = max(r.year for r in records if r.year)

        # Aggregate by country
        country_totals = {}
        for r in records:
            if r.year != year or r.quantity is None:
                continue
            if r.country not in country_totals:
                country_totals[r.country] = {
                    "country": r.country,
                    "country_iso": r.country_iso,
                    "quantity": 0,
                    "units": r.units,
                    "year": year,
                }
            country_totals[r.country]["quantity"] += r.quantity

        ranked = sorted(
            country_totals.values(),
            key=lambda x: x["quantity"],
            reverse=True,
        )

        total = sum(r["quantity"] for r in ranked)
        for i, r in enumerate(ranked[:top_n], 1):
            r["rank"] = i
            r["share_percent"] = round((r["quantity"] / total * 100) if total else 0, 2)

        return ranked[:top_n]


# ============================================================================
# CLAIMM (EDX) Client
# ============================================================================


class CLAIMMClient:
    """Client for NETL EDX CLAIMM API."""

    def __init__(self):
        settings = get_settings()
        self._core = CoreCLAIMMClient(
            base_url=settings.edx_base_url,
            api_key=settings.edx_api_key,
            timeout=30.0,
        )

    async def search_datasets(
        self,
        query: str | None = None,
        tags: list[str] | None = None,
        limit: int = 20,
    ) -> list[DatasetInfo]:
        """Search CLAIMM datasets."""
        core_datasets = await self._core.search_datasets(query=query, tags=tags, limit=limit)
        return [
            DatasetInfo(
                source=ds.source,
                id=ds.id,
                title=ds.title,
                description=ds.description,
                tags=ds.tags,
                resources=[
                    {
                        "id": r.id,
                        "name": r.name,
                        "format": r.format,
                        "size": r.size,
                        "url": r.url,
                    }
                    for r in ds.resources
                ],
            )
            for ds in core_datasets
        ]

    async def get_dataset(self, dataset_id: str) -> DatasetInfo | None:
        """Get dataset details."""
        core_dataset = await self._core.get_dataset(dataset_id)
        if not core_dataset:
            return None
        return DatasetInfo(
            source=core_dataset.source,
            id=core_dataset.id,
            title=core_dataset.title,
            description=core_dataset.description,
            tags=core_dataset.tags,
            resources=[
                {
                    "id": r.id,
                    "name": r.name,
                    "format": r.format,
                    "size": r.size,
                    "url": r.url,
                }
                for r in core_dataset.resources
            ],
        )

    async def get_categories(self) -> dict[str, int]:
        """Get dataset categories and counts."""
        return await self._core.get_categories()


# ============================================================================
# Unified Client
# ============================================================================


class UnifiedClient:
    """Unified client for both CLAIMM and BGS data sources."""

    def __init__(self):
        self.bgs = BGSClient()
        self.claimm = CLAIMMClient()

    async def search_all(
        self,
        query: str,
        sources: list[str] | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Search across all data sources."""
        results = {"query": query, "sources": {}}
        sources = sources or ["CLAIMM", "BGS"]

        if "CLAIMM" in sources:
            try:
                claimm_results = await self.claimm.search_datasets(query=query, limit=limit)
                results["sources"]["CLAIMM"] = {
                    "count": len(claimm_results),
                    "datasets": [ds.model_dump() for ds in claimm_results],
                }
            except (httpx.HTTPError, OSError, KeyError) as e:
                results["sources"]["CLAIMM"] = {"error": str(e)}

        if "BGS" in sources:
            try:
                # Map common terms to BGS commodities
                commodity_map = {
                    "lithium": "lithium minerals",
                    "cobalt": "cobalt, mine",
                    "nickel": "nickel, mine",
                    "rare earth": "rare earth minerals",
                    "graphite": "graphite",
                    "copper": "copper, mine",
                    "manganese": "manganese ore",
                }

                bgs_commodity = None
                query_lower = query.lower()
                for term, commodity in commodity_map.items():
                    if term in query_lower:
                        bgs_commodity = commodity
                        break

                if bgs_commodity:
                    bgs_results = await self.bgs.search_production(
                        commodity=bgs_commodity, limit=limit
                    )
                    results["sources"]["BGS"] = {
                        "commodity": bgs_commodity,
                        "count": len(bgs_results),
                        "records": [r.model_dump() for r in bgs_results[:limit]],
                    }
                else:
                    results["sources"]["BGS"] = {
                        "message": "Specify a mineral (lithium, cobalt, nickel, etc.) for BGS data"
                    }
            except (httpx.HTTPError, OSError, KeyError) as e:
                results["sources"]["BGS"] = {"error": str(e)}

        return results

    async def get_overview(self) -> dict[str, Any]:
        """Get overview of all data sources."""
        overview = {
            "sources": {
                "CLAIMM": {
                    "name": "NETL EDX CLAIMM",
                    "description": "US Critical Minerals and Materials datasets",
                    "url": "https://edx.netl.doe.gov/edxapps/claimm/",
                    "data_types": ["Datasets", "CSV files", "Schemas"],
                },
                "BGS": {
                    "name": "BGS World Mineral Statistics",
                    "description": "Global mineral production and trade statistics",
                    "url": "https://www.bgs.ac.uk/mineralsuk/statistics/world-mineral-statistics/",
                    "data_types": ["Production", "Imports", "Exports"],
                    "time_range": "1970-2023",
                },
            }
        }

        # Get CLAIMM categories
        try:
            overview["sources"]["CLAIMM"]["categories"] = await self.claimm.get_categories()
        except (httpx.HTTPError, OSError, KeyError):
            pass

        # Get BGS commodities
        overview["sources"]["BGS"]["commodities"] = self.bgs.CRITICAL_MINERALS

        return overview
