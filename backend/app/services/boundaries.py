"""Resolve OpenStreetMap search results to polygon boundaries via Nominatim."""
from shapely.geometry import shape, mapping
from shapely.validation import explain_validity
from app.services.nominatim import get_json


class BoundaryUnavailable(RuntimeError):
    pass


async def lookup_boundary(osm_type: str, osm_id: int) -> dict:
    type_code = {"node": "N", "way": "W", "relation": "R"}.get(osm_type.lower())
    if not type_code or not isinstance(osm_id, int) or osm_id <= 0:
        raise BoundaryUnavailable("The selected search result does not include a usable map feature ID.")

    try:
        results = await get_json(
            "lookup",
            {
                "osm_ids": f"{type_code}{osm_id}",
                "format": "jsonv2",
                "polygon_geojson": 1,
                "polygon_threshold": 0.005,
            },
        )
    except Exception as exc:
        raise BoundaryUnavailable("The location boundary service is temporarily unavailable.") from exc

    if not isinstance(results, list) or not results:
        raise BoundaryUnavailable("No geographic boundary was found for this search result.")

    geometry = results[0].get("geojson")
    if not isinstance(geometry, dict) or geometry.get("type") not in ("Polygon", "MultiPolygon"):
        raise BoundaryUnavailable(
            "This search result is a point or place marker, not a complete administrative boundary. "
            "Try the city, district or municipal-area result instead."
        )

    try:
        geom = shape(geometry)
    except Exception as exc:
        raise BoundaryUnavailable("The location boundary could not be interpreted.") from exc

    if geom.is_empty or not geom.is_valid:
        raise BoundaryUnavailable("The location boundary is incomplete or invalid: " + explain_validity(geom))
    minx, miny, maxx, maxy = geom.bounds
    if minx < -180 or maxx > 180 or miny < -90 or maxy > 90:
        raise BoundaryUnavailable("The location boundary has invalid longitude/latitude coordinates.")

    display_geom = geom.simplify(0.002, preserve_topology=True)
    return {
        "geometry": mapping(geom),
        "display_geometry": mapping(display_geom),
        "osm_type": osm_type.lower(),
        "osm_id": osm_id,
        "boundary_name": results[0].get("display_name"),
        "boundary_type": results[0].get("type") or results[0].get("category"),
    }
