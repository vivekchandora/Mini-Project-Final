"""WorldPop Global2 v3 client with safe large-polygon splitting.

WorldPop's documented no-key limit is 100,000 km² per request. Large user
polygons are partitioned in an equal-area projection and queried sequentially.
"""
import logging
import math
import os

import httpx
from pyproj import Transformer
from shapely.geometry import box, mapping
from shapely.ops import transform

BASE = os.getenv("WORLDPOP_API_BASE_URL", "https://api.worldpop.org/v3").rstrip("/")
API_KEY = os.getenv("WORLDPOP_API_KEY", "").strip()
DOCS_URL = "https://api.worldpop.org/v3/documentation"
DATASET = "WorldPop Global2 R2025A v1, approximately 100 m (3 arc-seconds)"
CITATION = (
    "Bondarenko et al. (2025), Constrained estimates of 2015-2030 total number "
    "of people per grid square at approximately 100 m, WorldPop, University "
    "of Southampton. DOI: 10.5258/SOTON/WP00839."
)

# Stay well below WorldPop's documented 100,000 km² no-key area limit.
MAX_PART_AREA_KM2 = 50_000.0
MAX_PARTS = 200
EQUAL_AREA_CRS = "EPSG:6933"
TO_EQUAL_AREA = Transformer.from_crs("EPSG:4326", EQUAL_AREA_CRS, always_xy=True).transform
TO_WGS84 = Transformer.from_crs(EQUAL_AREA_CRS, "EPSG:4326", always_xy=True).transform
logger = logging.getLogger(__name__)


class WorldPopUnavailable(RuntimeError):
    pass


def _polygonal_parts(geom):
    """Yield Polygon members only; ignore line/point remnants from intersections."""
    if geom.is_empty:
        return
    if geom.geom_type == "Polygon":
        yield geom
    elif geom.geom_type in ("MultiPolygon", "GeometryCollection"):
        for member in geom.geoms:
            yield from _polygonal_parts(member)


def _split_large_geometry(geojson):
    """Partition a WGS84 polygon into non-overlapping equal-area grid pieces."""
    from shapely.geometry import shape

    geom = shape(geojson)
    projected = transform(TO_EQUAL_AREA, geom)
    area_km2 = projected.area / 1_000_000.0
    if area_km2 <= MAX_PART_AREA_KM2:
        return [geojson], area_km2

    minx, miny, maxx, maxy = projected.bounds
    width = maxx - minx
    height = maxy - miny
    bbox_area_km2 = (width * height) / 1_000_000.0
    if width <= 0 or height <= 0 or bbox_area_km2 <= 0:
        raise WorldPopUnavailable("The selected polygon could not be divided into valid areas.")

    # Choose a grid whose individual bounding rectangles are <= 50,000 km².
    aspect = width / height
    scale = math.sqrt(bbox_area_km2 / MAX_PART_AREA_KM2)
    columns = max(1, math.ceil(scale * math.sqrt(aspect)))
    rows = max(1, math.ceil(scale / math.sqrt(aspect)))
    if columns * rows > MAX_PARTS:
        raise WorldPopUnavailable(
            f"This boundary is too large or complex to process safely ({columns * rows} sections required)."
        )

    dx = width / columns
    dy = height / rows
    pieces = []
    for row in range(rows):
        y0 = miny + row * dy
        y1 = maxy if row == rows - 1 else miny + (row + 1) * dy
        for col in range(columns):
            x0 = minx + col * dx
            x1 = maxx if col == columns - 1 else minx + (col + 1) * dx
            clipped = projected.intersection(box(x0, y0, x1, y1))
            polygons = list(_polygonal_parts(clipped))
            if not polygons:
                continue
            # Preserve islands/multipart intersections as one MultiPolygon request.
            from shapely.geometry import MultiPolygon, mapping
            valid_polys = [p for p in polygons if not p.is_empty and p.area > 1.0]
            if not valid_polys:
                continue
            if len(valid_polys) == 1:
                part_projected = valid_polys[0]
            else:
                part_projected = MultiPolygon(valid_polys)
            part_wgs84 = transform(TO_WGS84, part_projected)
            if not part_wgs84.is_valid:
                part_wgs84 = part_wgs84.buffer(0)
            if part_wgs84.is_empty:
                continue
            pieces.append(mapping(part_wgs84))

    if not pieces or len(pieces) > MAX_PARTS:
        raise WorldPopUnavailable("The selected polygon could not be divided into valid WorldPop sections.")
    return pieces, area_km2


def _read_api_error(response):
    """Extract a short, non-secret diagnostic from a WorldPop error response."""
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    if isinstance(payload, dict):
        code = payload.get("error")
        message = payload.get("message")
        request_id = payload.get("request_id")
        bits = [str(v) for v in (code, message) if v]
        if request_id:
            bits.append(f"request_id={request_id}")
        if bits:
            return "; ".join(bits)[:700]
    return (response.text or f"HTTP {response.status_code}")[:500]


async def _request_one(client, geojson, year):
    headers = {"Accept": "application/json"}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    try:
        response = await client.post(
            f"{BASE}/population",
            json={"geojson": geojson, "year": year},
            headers=headers,
        )
    except httpx.TimeoutException as exc:
        raise WorldPopUnavailable("WorldPop timed out while processing one section. Please try again.") from exc
    except httpx.RequestError as exc:
        logger.warning("WorldPop connection failure: %s", type(exc).__name__)
        raise WorldPopUnavailable("Could not connect to WorldPop. Please try again later.") from exc

    if response.is_error:
        diagnostic = _read_api_error(response)
        logger.warning("WorldPop returned HTTP %s: %s", response.status_code, diagnostic)
        if response.status_code == 413:
            raise WorldPopUnavailable(
                f"WorldPop rejected a section because of its area or processing complexity ({diagnostic})."
            )
        if response.status_code == 429:
            raise WorldPopUnavailable(
                f"WorldPop rate or concurrency limit reached ({diagnostic}). Please wait and try again."
            )
        raise WorldPopUnavailable(
            f"WorldPop returned HTTP {response.status_code} ({diagnostic}). Please try again later."
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise WorldPopUnavailable("WorldPop returned invalid JSON.") from exc
    if not isinstance(data, dict):
        raise WorldPopUnavailable("WorldPop returned an unexpected response format.")
    return data


def _validate_result(data, year):
    total = data.get("total_population")
    area = data.get("area_km2")
    density = data.get("population_density")
    data_year = data.get("data_year")
    source = data.get("data_source")

    if not isinstance(total, (int, float)) or isinstance(total, bool) or not math.isfinite(float(total)) or total < 0:
        raise WorldPopUnavailable("WorldPop response did not contain a valid total_population.")
    if not isinstance(area, (int, float)) or isinstance(area, bool) or not math.isfinite(float(area)) or area <= 0:
        raise WorldPopUnavailable("WorldPop response did not contain a valid area.")
    if not isinstance(density, (int, float)) or isinstance(density, bool) or not math.isfinite(float(density)) or density < 0:
        raise WorldPopUnavailable("WorldPop response did not contain a valid population density.")
    if data_year != year:
        raise WorldPopUnavailable("WorldPop returned a different reference year than requested.")
    if not isinstance(source, str) or not source.strip():
        raise WorldPopUnavailable("WorldPop did not identify its population dataset.")
    return float(total), float(area), source


async def estimate(geojson: dict, year: int) -> dict:
    """Return a validated WorldPop result, splitting large areas into safe pieces."""
    if not 2015 <= year <= 2030:
        raise WorldPopUnavailable("WorldPop supports reference years 2015–2030.")

    pieces, original_area_km2 = _split_large_geometry(geojson)
    totals = []
    areas = []
    sources = []
    processing_ms = 0

    # Sequential requests comply with WorldPop's concurrency guidance.
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=15.0)) as client:
            for index, part in enumerate(pieces, start=1):
                data = await _request_one(client, part, year)
                total, area, source = _validate_result(data, year)
                totals.append(total)
                areas.append(area)
                sources.append(source)
                elapsed = data.get("processing_time_ms")
                if isinstance(elapsed, (int, float)) and math.isfinite(float(elapsed)):
                    processing_ms += int(elapsed)
    except WorldPopUnavailable as exc:
        if len(pieces) > 1:
            raise WorldPopUnavailable(
                f"Large-area analysis stopped at section {len(totals) + 1} of {len(pieces)}. {exc}"
            ) from exc
        raise

    total_population = sum(totals)
    returned_area = sum(areas)
    if returned_area <= 0:
        raise WorldPopUnavailable("WorldPop returned no usable area for the selected boundary.")
    density = total_population / returned_area

    return {
        "estimated_population": int(round(total_population)),
        "population_value": round(total_population, 2),
        "area_sq_km": round(returned_area, 4),
        "population_density": round(density, 2),
        "reference_year": int(year),
        "data_source": sources[0],
        "dataset": DATASET,
        "source_url": DOCS_URL,
        "citation": CITATION,
        "estimate_type": "modelled gridded population estimate",
        "confidence": "Modelled gridded estimate. No universal numeric confidence interval is published for this individual polygon.",
        "resolution": "3 arc-seconds (approximately 100 m at the equator)",
        "release_status": "R2025A v1 public release; WorldPop describes this release as an alpha product",
        "method": "Top-down random-forest dasymetric redistribution of population totals using geospatial covariates.",
        "processing_time_ms": processing_ms,
        "worldpop_request_count": len(pieces),
        "area_was_split": len(pieces) > 1,
    }
