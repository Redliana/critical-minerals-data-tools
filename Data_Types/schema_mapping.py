import json
from datetime import datetime

import pandas as pd
import yaml

# ----------------------------
# Utility functions
# ----------------------------


def to_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def to_int(value):
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def extract_numeric_km(value):
    """
    Example: '12 km N of TownX' -> 12.0
    Falls back to None if parsing fails.
    """
    if value is None:
        return None
    s = str(value)
    tokens = s.replace(",", " ").split()
    for t in tokens:
        try:
            return float(t)
        except ValueError:
            continue
    return None


def map_value(raw, mapping_dict):
    if raw is None:
        return mapping_dict.get("default")
    key = str(raw).strip().lower()
    return mapping_dict.get(key, mapping_dict.get("default"))


def capacity_entry(row, mapping, args, defaults):
    """
    Build a single capacity entry object from a row.
    args:
      - year_field (or None)
      - value_field
      - product_field
    """
    value_field = args["value_field"]
    product_field = args.get("product_field")
    year_field = args.get("year_field")

    raw_value = row.get(value_field)
    if raw_value in (None, ""):
        return None

    value = to_float(raw_value)
    if value is None:
        return None

    # year: either from a column or left None
    year = None
    if year_field:
        year = to_int(row.get(year_field))

    product = None
    if product_field:
        product = row.get(product_field)

    entry = {
        "year": year,
        "product": product,
        "value": value,
        "unit": defaults.get("processing.design_capacity[].unit"),
        "source": defaults.get("processing.design_capacity[].source"),
    }
    return entry


# ----------------------------
# Mapping application
# ----------------------------


def set_nested(dct, path, value, append=False):
    """
    Set a nested value in a dict given a dotted path (e.g., 'location.country').
    If append=True, value is appended to a list at the final path.
    """
    if value is None:
        return

    parts = path.split(".")
    current = dct
    for p in parts[:-1]:
        if p not in current or not isinstance(current[p], dict):
            current[p] = {}
        current = current[p]
    last = parts[-1]

    if append:
        if last not in current or not isinstance(current[last], list):
            current[last] = []
        current[last].append(value)
    else:
        current[last] = value


def load_mapping(mapping_path):
    with open(mapping_path) as f:
        mapping = yaml.safe_load(f)
    return mapping


def apply_mapping_to_row(row, mapping):
    record = {}

    defaults = mapping.get("defaults", {})
    value_mappings = mapping.get("value_mappings", {})
    fields = mapping.get("fields", {})

    # apply defaults
    for path, v in defaults.items():
        # dot paths like metadata.source_system
        set_nested(record, path, v)

    # process each field
    for source_col, spec in fields.items():
        raw = row.get(source_col)

        path = spec["path"]
        transform_name = spec.get("transform")
        transform_args = spec.get("transform_args", {})

        value = raw

        if transform_name == "to_float":
            value = to_float(raw)
        elif transform_name == "to_int":
            value = to_int(raw)
        elif transform_name == "to_string":
            value = None if raw is None else str(raw)
        elif transform_name == "extract_numeric_km":
            value = extract_numeric_km(raw)
        elif transform_name == "map_value":
            mapping_key = transform_args["mapping_key"]
            value = map_value(raw, value_mappings.get(mapping_key, {}))
        elif transform_name == "capacity_entry":
            value = capacity_entry(row, mapping, transform_args, defaults)
        else:
            # no transform or unknown transform: keep raw
            value = raw

        if value is None:
            continue

        # capacity_entry produces an object that should be appended
        if transform_name == "capacity_entry":
            set_nested(record, path, value, append=True)
        else:
            set_nested(record, path, value, append=False)

    # ingest timestamp if not already set
    meta = record.setdefault("metadata", {})
    if "ingest_timestamp" not in meta:
        meta["ingest_timestamp"] = datetime.utcnow().isoformat() + "Z"

    return record


def ingest_csv_to_jsonl(csv_path, mapping_path, output_jsonl_path):
    mapping = load_mapping(mapping_path)
    df = pd.read_csv(csv_path, dtype=str)  # keep as strings; we cast manually

    with open(output_jsonl_path, "w", encoding="utf-8") as out_f:
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            record = apply_mapping_to_row(row_dict, mapping)
            out_f.write(json.dumps(record) + "\n")


if __name__ == "__main__":
    # Example usage:
    # ingest_csv_to_jsonl(
    #     csv_path="data/Copper_mining_synthetic_10000.csv",
    #     mapping_path="etl/mappings/copper_mining_mapping.yaml",
    #     output_jsonl_path="out/copper_mining_canonical.jsonl"
    # )
    pass
