"""Import official Census A-04 Class I-VI XLSX workbooks into the city reference CSV.

Download the Class I-VI workbooks from the Census of India NADA catalogue.
This script imports only rows whose census year is 2011.
"""
import argparse
import csv
import os
import re
import sys

OUTPUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "census_2011_city_reference.csv")
SOURCE = "Census of India 2011 A-04 town/urban-agglomeration tables"


def norm(value):
    return re.sub(r"\s+", " ", str(value or "").replace("\n", " ").strip()).casefold()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("workbooks", nargs="+", help="Census A-04 Class I-VI .xlsx files")
    args = parser.parse_args()
    try:
        from openpyxl import load_workbook
    except ImportError:
        print("Missing optional dependency. Run: python -m pip install openpyxl", file=sys.stderr)
        return 2

    rows_by_name = {}
    if os.path.exists(OUTPUT):
        with open(OUTPUT, newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                rows_by_name[norm(row["canonical_name"])] = row

    imported = 0
    for path in args.workbooks:
        book = load_workbook(path, read_only=True, data_only=True)
        sheet = book.active
        values = list(sheet.iter_rows(values_only=True))
        header_row = None
        for idx, row in enumerate(values[:40]):
            labels = [norm(v) for v in row]
            if any("name of town" in x or "town/urban agglomeration" in x for x in labels) \
               and any("census year" in x for x in labels) \
               and any(x == "persons" or x.endswith(" persons") for x in labels):
                header_row = idx
                break
        if header_row is None:
            print(f"Skipped {path}: could not identify the A-04 header row")
            continue

        labels = [norm(v) for v in values[header_row]]
        def col(match):
            return next((i for i, label in enumerate(labels) if match(label)), None)

        name_i = col(lambda x: "name of town" in x or "town/urban agglomeration" in x)
        year_i = col(lambda x: "census year" in x)
        pop_i = col(lambda x: x == "persons" or x.endswith(" persons"))
        status_i = col(lambda x: "urban status" in x)
        state_i = col(lambda x: "india/state/district" in x or x == "state")
        if None in (name_i, year_i, pop_i):
            print(f"Skipped {path}: required columns not found")
            continue

        current_name = ""
        for row in values[header_row + 1:]:
            if name_i >= len(row):
                continue
            raw_name = row[name_i]
            if raw_name not in (None, ""):
                current_name = str(raw_name).strip()
            if not current_name:
                continue
            try:
                year = int(float(row[year_i]))
                population = int(float(row[pop_i]))
            except (TypeError, ValueError, IndexError):
                continue
            if year != 2011 or population < 0:
                continue
            status = str(row[status_i] or "") if status_i is not None and status_i < len(row) else ""
            unit_type = "Urban Agglomeration" if "ua" in status.casefold() or "agglomeration" in status.casefold() else "Town"
            canonical = current_name
            aliases = "|".join(dict.fromkeys([canonical, re.sub(r"\s+U\.?A\.?$", "", canonical, flags=re.I)]))
            rows_by_name[norm(canonical)] = {
                "canonical_name": canonical,
                "aliases": aliases,
                "state": (
                    str(row[state_i] or "").strip().split("/")[1].strip()
                    if state_i is not None and state_i < len(row)
                    and "/" in str(row[state_i] or "")
                    else (str(row[state_i] or "").strip() if state_i is not None and state_i < len(row) else "")
                ),
                "population_2011": str(population),
                "unit_type": unit_type,
                "source_table": SOURCE,
                "source_url": "https://censusindia.gov.in/census.website/en/data/tables",
            }
            imported += 1
        book.close()

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, "w", newline="", encoding="utf-8") as handle:
        fields = ["canonical_name", "aliases", "state", "population_2011", "unit_type", "source_table", "source_url"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows_by_name.values())
    print(f"Imported/updated {imported} 2011 city/urban-agglomeration rows. Total reference rows: {len(rows_by_name)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
