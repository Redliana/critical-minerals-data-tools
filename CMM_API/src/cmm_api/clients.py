"""Data clients for CLAIMM (EDX) and BGS APIs."""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel

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
        self.base_url = settings.bgs_base_url
        self.timeout = 60.0

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
        params = {"limit": limit, "bgs_statistic_type_trans": statistic_type}

        if commodity:
            params["bgs_commodity_trans"] = commodity
        if country:
            if len(country) <= 3:
                params["country_iso3_code"] = country.upper()
            else:
                params["country_trans"] = country

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/items",
                params=params,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json()

        records = []
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            year_str = props.get("year", "")
            year = int(year_str[:4]) if year_str and len(year_str) >= 4 else None

            # Filter by year range
            if year_from and year and year < year_from:
                continue
            if year_to and year and year > year_to:
                continue

            records.append(
                MineralRecord(
                    source="BGS",
                    commodity=props.get("bgs_commodity_trans", ""),
                    country=props.get("country_trans"),
                    country_iso=props.get("country_iso3_code"),
                    year=year,
                    quantity=props.get("quantity"),
                    units=props.get("units"),
                    statistic_type=statistic_type,
                    notes=props.get("concat_table_notes_text"),
                )
            )

        return sorted(records, key=lambda x: x.year or 0, reverse=True)[:limit]

    async def get_commodities(self, critical_only: bool = False) -> list[str]:
        """Get list of BGS commodities."""
        if critical_only:
            return self.CRITICAL_MINERALS.copy()

        commodities = set()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for offset in [0, 5000]:
                response = await client.get(
                    f"{self.base_url}/items",
                    params={"limit": 5000, "offset": offset},
                    headers={"Accept": "application/json"},
                )
                if response.status_code != 200:
                    break
                data = response.json()
                for feature in data.get("features", []):
                    commodity = feature.get("properties", {}).get("bgs_commodity_trans")
                    if commodity:
                        commodities.add(commodity)

        return sorted(commodities)

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
        self.base_url = settings.edx_base_url
        self.api_key = settings.edx_api_key
        self.timeout = 30.0

    def _get_headers(self) -> dict:
        """Get API headers."""
        headers = {"User-Agent": "EDX-USER", "Content-Type": "application/json"}
        if self.api_key:
            headers["X-CKAN-API-Key"] = self.api_key
        return headers

    async def _request(self, endpoint: str, params: dict | None = None) -> dict:
        """Make API request."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/{endpoint}",
                params=params,
                headers=self._get_headers(),
            )
            response.raise_for_status()
            result = response.json()

            if not result.get("success", False):
                raise Exception(f"EDX API error: {result.get('error', {})}")

            return result.get("result", {})

    async def search_datasets(
        self,
        query: str | None = None,
        tags: list[str] | None = None,
        limit: int = 20,
    ) -> list[DatasetInfo]:
        """Search CLAIMM datasets."""
        params: dict[str, Any] = {"rows": limit, "start": 0}

        # Always include claimm in query
        search_query = f"claimm {query}" if query else "claimm"
        params["q"] = search_query

        if tags:
            params["fq"] = " AND ".join(f"tags:{t}" for t in tags)

        result = await self._request("package_search", params)

        datasets = []
        for pkg in result.get("results", []):
            resources = [
                {
                    "id": r.get("id"),
                    "name": r.get("name"),
                    "format": r.get("format"),
                    "size": r.get("size"),
                    "url": f"https://edx.netl.doe.gov/resource/{r.get('id')}/download",
                }
                for r in pkg.get("resources", [])
            ]

            datasets.append(
                DatasetInfo(
                    source="CLAIMM",
                    id=pkg.get("id", ""),
                    title=pkg.get("title", pkg.get("name", "")),
                    description=pkg.get("notes"),
                    tags=[t.get("name", "") for t in pkg.get("tags", [])],
                    resources=resources,
                )
            )

        return datasets

    async def get_dataset(self, dataset_id: str) -> DatasetInfo | None:
        """Get dataset details."""
        try:
            result = await self._request("package_show", {"id": dataset_id})

            resources = [
                {
                    "id": r.get("id"),
                    "name": r.get("name"),
                    "format": r.get("format"),
                    "size": r.get("size"),
                    "url": f"https://edx.netl.doe.gov/resource/{r.get('id')}/download",
                }
                for r in result.get("resources", [])
            ]

            return DatasetInfo(
                source="CLAIMM",
                id=result.get("id", ""),
                title=result.get("title", result.get("name", "")),
                description=result.get("notes"),
                tags=[t.get("name", "") for t in result.get("tags", [])],
                resources=resources,
            )
        except Exception:
            return None

    async def get_categories(self) -> dict[str, int]:
        """Get dataset categories and counts."""
        datasets = await self.search_datasets(limit=200)

        categories = {}
        keywords = {
            "Rare Earth Elements": ["rare earth", "ree", "lanthanide"],
            "Produced Water": ["produced water", "newts", "brine"],
            "Coal & Coal Byproducts": ["coal", "coal ash", "fly ash"],
            "Mine Waste": ["mine waste", "tailings", "mining"],
            "Lithium": ["lithium"],
            "Geochemistry": ["geochemistry", "geochemical"],
            "Geology": ["geology", "geological", "geophysic"],
        }

        for ds in datasets:
            text = f"{ds.title} {ds.description or ''} {' '.join(ds.tags)}".lower()
            categorized = False

            for category, kws in keywords.items():
                if any(kw in text for kw in kws):
                    categories[category] = categories.get(category, 0) + 1
                    categorized = True
                    break

            if not categorized:
                categories["Other"] = categories.get("Other", 0) + 1

        return categories


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
            except Exception as e:
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
            except Exception as e:
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
        except Exception:
            pass

        # Get BGS commodities
        overview["sources"]["BGS"]["commodities"] = self.bgs.CRITICAL_MINERALS

        return overview
