from shapely.geometry import shape
from shapely.validation import explain_validity
from pyproj import Transformer
from shapely.ops import transform

def validate_polygon(data):
    if not isinstance(data,dict) or data.get("type") not in ("Polygon","MultiPolygon"):
        raise ValueError("A GeoJSON Polygon or MultiPolygon is required.")
    geom=shape(data)
    if geom.is_empty: raise ValueError("Polygon is empty.")
    if not geom.is_valid: raise ValueError("Invalid polygon: "+explain_validity(geom))
    if len(str(data))>1_000_000: raise ValueError("Geometry is too large.")
    minx,miny,maxx,maxy=geom.bounds
    if minx < -180 or maxx > 180 or miny < -90 or maxy > 90: raise ValueError("Coordinates must be EPSG:4326 longitude/latitude.")
    return geom

def area_sq_km(geom):
    fn=Transformer.from_crs("EPSG:4326","EPSG:6933",always_xy=True).transform
    return round(transform(fn,geom).area/1_000_000,4)
