"""BGS World Mineral Statistics client backed by cmm_data shared clients."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from cmm_data.clients import BGSClient as CoreBGSClient


class MineralRecord(BaseModel):
    """A single mineral production/trade record."""

    commodity: str
    sub_commodity: str | None = None
    statistic_type: str
    country: str
    country_iso2: str | None = None
    country_iso3: str | None = None
    year: int | None = None
    quantity: float | None = None
    units: str | None = None
    yearbook_table: str | None = None
    notes: str | None = None


class BGSClient:
    """Compatibility wrapper for BGS client methods used by MCP/API servers."""

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
        "bismuth, mine",
        "selenium, refined",
        "rhenium",
        "strontium minerals",
        "copper, mine",
        "copper, refined",
        "zinc, mine",
        "lead, mine",
        "tin, mine",
        "aluminium, primary",
        "bauxite",
        "fluorspar",
        "magnesite",
        "phosphate rock",
        "barytes",
        "borates",
        "gold, mine",
        "silver, mine",
        "antimony, mine",
        "molybdenum, mine",
        "iron ore",
    ]

    def __init__(self):
        self._core = CoreBGSClient()

    @staticmethod
    def _to_record(core_record: Any) -> MineralRecord:
        return MineralRecord(
            commodity=core_record.commodity,
            statistic_type=core_record.statistic_type or "Production",
            country=core_record.country or "",
            country_iso2=core_record.country_iso2,
            country_iso3=core_record.country_iso3,
            year=core_record.year,
            quantity=core_record.quantity,
            units=core_record.units,
            notes=core_record.notes,
        )

    async def get_commodities(self) -> list[str]:
        return await self._core.get_commodities()

    async def get_countries(self, commodity: str | None = None) -> list[dict[str, str]]:
        params = {"bgs_commodity_trans": commodity} if commodity else None
        raw = await self._core._request(params=params, limit=5000)  # noqa: SLF001
        countries: dict[str, dict[str, str]] = {}
        for feature in raw.get("features", []):
            props = feature.get("properties", {})
            country = props.get("country_trans")
            if not country:
                continue
            if country not in countries:
                countries[country] = {
                    "name": country,
                    "iso2": props.get("country_iso2_code"),
                    "iso3": props.get("country_iso3_code"),
                }
        return sorted(countries.values(), key=lambda item: item["name"])

    async def search_production(
        self,
        commodity: str | None = None,
        country: str | None = None,
        country_iso: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        statistic_type: str = "Production",
        limit: int = 1000,
    ) -> list[MineralRecord]:
        records = await self._core.search_production(
            commodity=commodity,
            country=country,
            country_iso=country_iso,
            year_from=year_from,
            year_to=year_to,
            statistic_type=statistic_type,
            limit=limit,
        )
        return [self._to_record(record) for record in records]

    async def get_time_series(
        self,
        commodity: str,
        country: str | None = None,
        country_iso: str | None = None,
        statistic_type: str = "Production",
    ) -> list[MineralRecord]:
        records = await self.search_production(
            commodity=commodity,
            country=country,
            country_iso=country_iso,
            statistic_type=statistic_type,
            limit=5000,
        )
        records.sort(key=lambda x: x.year or 0)
        return records

    async def get_commodity_by_country(
        self,
        commodity: str,
        year: int | None = None,
        statistic_type: str = "Production",
        top_n: int = 20,
    ) -> list[dict[str, Any]]:
        records = await self.search_production(
            commodity=commodity,
            statistic_type=statistic_type,
            limit=5000,
        )
        if not records:
            return []

        if year is None:
            year_candidates = [r.year for r in records if r.year is not None]
            if not year_candidates:
                return []
            year = max(year_candidates)

        country_totals: dict[str, dict[str, Any]] = {}
        for record in records:
            if record.year != year or record.quantity is None:
                continue
            if record.country not in country_totals:
                country_totals[record.country] = {
                    "country": record.country,
                    "country_iso3": record.country_iso3,
                    "quantity": 0.0,
                    "units": record.units,
                    "year": year,
                }
            country_totals[record.country]["quantity"] += float(record.quantity)

        ranked = sorted(country_totals.values(), key=lambda x: x["quantity"], reverse=True)
        return ranked[:top_n]

    async def compare_countries(
        self,
        commodity: str,
        countries: list[str],
        year_from: int | None = None,
        year_to: int | None = None,
        statistic_type: str = "Production",
    ) -> dict[str, list[dict[str, Any]]]:
        result = {}
        for country in countries:
            records = await self.search_production(
                commodity=commodity,
                country=country if len(country) > 3 else None,
                country_iso=country if len(country) <= 3 else None,
                year_from=year_from,
                year_to=year_to,
                statistic_type=statistic_type,
                limit=1000,
            )

            country_name = records[0].country if records else country
            result[country_name] = [
                {"year": r.year, "quantity": r.quantity, "units": r.units}
                for r in sorted(records, key=lambda x: x.year or 0)
            ]
        return result

    def get_critical_minerals(self) -> list[str]:
        return self.CRITICAL_MINERALS.copy()
