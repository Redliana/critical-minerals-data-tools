#!/usr/bin/env python3
"""Download BGS World Mineral Statistics for critical minerals."""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from urllib.parse import quote

import httpx

# BGS OGC API endpoint
BGS_API_BASE = "https://ogcapi.bgs.ac.uk/collections/world-mineral-statistics/items"

# Critical minerals to download (commodity names as they appear in BGS data)
CRITICAL_MINERALS = [
    # Battery minerals
    "lithium minerals",
    "cobalt, mine",
    "cobalt, refined",
    "nickel, mine",
    "nickel, smelter/refinery",
    "graphite",
    "manganese ore",
    # Rare earths
    "rare earth minerals",
    "rare earth oxides",
    # Strategic metals
    "platinum group metals, mine",
    "vanadium, mine",
    "tungsten, mine",
    "chromium ores and concentrates",
    "tantalum and niobium minerals",
    "titanium minerals",
    # Technology minerals
    "gallium, primary",
    "germanium metal",
    "indium, refinery",
    "beryl",
    "bismuth, mine",
    "selenium, refined",
    "rhenium",
    "strontium minerals",
    # Base metals (important for supply chain)
    "copper, mine",
    "copper, refined",
    "zinc, mine",
    "zinc, slab",
    "lead, mine",
    "lead, refined",
    "tin, mine",
    "tin, smelter",
    "aluminium, primary",
    "bauxite",
    "alumina",
    # Industrial minerals
    "fluorspar",
    "magnesite",
    "phosphate rock",
    "barytes",
    "borates",
    # Precious metals
    "gold, mine",
    "silver, mine",
    # Other critical
    "antimony, mine",
    "molybdenum, mine",
    "iron ore",
]

# Statistics types to fetch
STAT_TYPES = ["Production", "Imports", "Exports"]


def fetch_commodity_data(
    commodity: str,
    stat_type: str = "Production",
    limit: int = 10000,
) -> list[dict]:
    """Fetch all records for a commodity from BGS API."""
    all_records = []
    offset = 0

    while True:

        # Build URL with encoded parameters
        url = f"{BGS_API_BASE}?limit={limit}&offset={offset}"
        url += f"&bgs_commodity_trans={quote(commodity)}"
        url += f"&bgs_statistic_type_trans={quote(stat_type)}"

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.get(url, headers={"Accept": "application/json"})
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPStatusError, httpx.ConnectError, ConnectionError) as e:
            print(f"    Error fetching {commodity} ({stat_type}): {e}")
            break

        features = data.get("features", [])
        if not features:
            break

        for feature in features:
            props = feature.get("properties", {})
            record = {
                "commodity": props.get("bgs_commodity_trans", ""),
                "sub_commodity": props.get("bgs_sub_commodity_trans", ""),
                "statistic_type": props.get("bgs_statistic_type_trans", ""),
                "country": props.get("country_trans", ""),
                "country_iso2": props.get("country_iso2_code", ""),
                "country_iso3": props.get("country_iso3_code", ""),
                "year": props.get("year", "")[:4] if props.get("year") else "",
                "quantity": props.get("quantity", ""),
                "units": props.get("units", ""),
                "yearbook_table": props.get("yearbook_table_trans", ""),
                "erml_commodity": props.get("erml_commodity", ""),
                "erml_group": props.get("erml_group", ""),
                "table_notes": props.get("concat_table_notes_text", ""),
                "figure_notes": props.get("concat_figure_notes_text", ""),
            }
            all_records.append(record)

        # Check if we got fewer records than limit (means we're done)
        if len(features) < limit:
            break

        offset += limit
        time.sleep(0.2)  # Rate limiting

    return all_records


def save_to_csv(records: list[dict], filepath: Path) -> None:
    """Save records to CSV file."""
    if not records:
        return

    fieldnames = [
        "commodity",
        "sub_commodity",
        "statistic_type",
        "country",
        "country_iso2",
        "country_iso3",
        "year",
        "quantity",
        "units",
        "yearbook_table",
        "erml_commodity",
        "erml_group",
        "table_notes",
        "figure_notes",
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def main():
    """Download all critical mineral data from BGS."""
    output_dir = Path(__file__).parent / "bgs_data"
    output_dir.mkdir(exist_ok=True)

    all_production_records = []
    all_trade_records = []
    summary = []

    print("=" * 60)
    print("BGS World Mineral Statistics Download")
    print("=" * 60)
    print(f"Output directory: {output_dir}")
    print(f"Commodities to fetch: {len(CRITICAL_MINERALS)}")
    print()

    for i, commodity in enumerate(CRITICAL_MINERALS, 1):
        print(f"[{i}/{len(CRITICAL_MINERALS)}] {commodity}")

        commodity_records = {"Production": [], "Imports": [], "Exports": []}

        for stat_type in STAT_TYPES:
            records = fetch_commodity_data(commodity, stat_type)
            commodity_records[stat_type] = records

            if records:
                print(f"    {stat_type}: {len(records)} records")

                if stat_type == "Production":
                    all_production_records.extend(records)
                else:
                    all_trade_records.extend(records)

            time.sleep(0.3)  # Rate limiting between requests

        # Save individual commodity file (production only for cleaner files)
        if commodity_records["Production"]:
            safe_name = commodity.replace(", ", "_").replace(" ", "_").replace("/", "_")
            commodity_file = output_dir / f"{safe_name}_production.csv"
            save_to_csv(commodity_records["Production"], commodity_file)

        # Track summary
        summary.append(
            {
                "commodity": commodity,
                "production_records": len(commodity_records["Production"]),
                "import_records": len(commodity_records["Imports"]),
                "export_records": len(commodity_records["Exports"]),
            }
        )

        time.sleep(0.5)  # Rate limiting between commodities

    # Save combined files
    print()
    print("Saving combined files...")

    # All production data
    production_file = output_dir / "bgs_critical_minerals_production.csv"
    save_to_csv(all_production_records, production_file)
    print(f"  Production data: {len(all_production_records)} records -> {production_file.name}")

    # All trade data
    trade_file = output_dir / "bgs_critical_minerals_trade.csv"
    save_to_csv(all_trade_records, trade_file)
    print(f"  Trade data: {len(all_trade_records)} records -> {trade_file.name}")

    # Summary file
    summary_file = output_dir / "bgs_download_summary.csv"
    with open(summary_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["commodity", "production_records", "import_records", "export_records"]
        )
        writer.writeheader()
        writer.writerows(summary)
    print(f"  Summary: {summary_file.name}")

    # Save as JSON too for programmatic access
    json_file = output_dir / "bgs_critical_minerals_production.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_production_records, f, indent=2)
    print(f"  JSON export: {json_file.name}")

    print()
    print("=" * 60)
    print("Download Complete!")
    print("=" * 60)
    print(f"Total production records: {len(all_production_records)}")
    print(f"Total trade records: {len(all_trade_records)}")
    print(f"Output directory: {output_dir}")

    # Print commodity summary
    print()
    print("Records by commodity:")
    for s in sorted(summary, key=lambda x: x["production_records"], reverse=True):
        if s["production_records"] > 0:
            print(f"  {s['commodity']:40} {s['production_records']:>6} production records")


if __name__ == "__main__":
    main()
