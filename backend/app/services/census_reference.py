"""Selected, clearly scoped Census 2011 urban-unit reference values."""
import csv
import os
import re
from functools import lru_cache

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "census_2011_city_reference.csv")


def _normalise(value: str) -> str:
    value = (value or "").lower()
    value = re.sub(r"[^a-z0-9 ]+", " ", value)
    return " ".join(value.split())


@lru_cache(maxsize=1)
def _rows():
    with open(DATA_FILE, newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def find_census_reference(*names):
    """Exact alias matching only; no fuzzy matches that could mix different cities."""
    wanted = set()
    for name in names:
        if not name:
            continue
        wanted.add(_normalise(name))
        # Nominatim display names are comma-separated; use their leading place
        # component for exact city aliases without fuzzy-matching arbitrary text.
        wanted.update(_normalise(part) for part in str(name).split(",")[:2])
    for row in _rows():
        aliases = {_normalise(row["canonical_name"])}
        aliases.update(_normalise(x) for x in row["aliases"].split("|"))
        if wanted.intersection(aliases):
            state = _normalise(row.get("state", ""))
            all_text = _normalise(" ".join(str(x or "") for x in names))
            if state and state not in all_text:
                continue
            return {
                "area_name": row["canonical_name"],
                "population": int(row["population_2011"]),
                "year": 2011,
                "unit_type": row["unit_type"],
                "state": row.get("state", ""),
                "source": row["source_table"],
                "source_url": row["source_url"],
                "scope_note": (
                    "Historical Census unit. Its boundary may differ from the selected "
                    "OpenStreetMap city or municipal boundary; do not treat the two "
                    "figures as a like-for-like comparison without checking the geography."
                ),
            }
    return None


def census_reference_count():
    return len(_rows())
