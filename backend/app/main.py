from datetime import date
import csv
import io
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.services.geospatial import validate_polygon, area_sq_km
from app.services.worldpop import estimate, WorldPopUnavailable, DOCS_URL, DATASET

app = FastAPI(title="Poupscan API", version="1.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Analysis(BaseModel):
    geojson: dict
    year: int = Field(default_factory=lambda: min(date.today().year, 2030), ge=2015, le=2030)
    location: str = "Custom selected area"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/v1/data-status")
def status():
    return {
        "worldpop": "WorldPop Global2 v3 population endpoint configured",
        "worldpop_dataset": DATASET,
        "worldpop_documentation": DOCS_URL,
        "census": "No official Census dataset imported; Census baseline is not yet available in this build",
        "admin_boundaries": "Custom user-drawn polygon; no automatic place search or boundary lookup",
        "ml_model": "Not trained; estimates come from the cited WorldPop gridded dataset",
    }


@app.post("/api/v1/population/custom-area")
async def analyse(a: Analysis):
    try:
        geom = validate_polygon(a.geojson)
        area = area_sq_km(geom)
    except Exception as exc:
        raise HTTPException(422, str(exc)) from exc
    try:
        result = await estimate(a.geojson, a.year)
    except WorldPopUnavailable as exc:
        raise HTTPException(
            503,
            {
                "message": str(exc),
                "area_sq_km": area,
                "estimated_population": None,
                "warning": "No population value was fabricated.",
            },
        ) from exc
    return {
        "location": a.location,
        "country": "India",
        **result,
        "area_sq_km": result["area_sq_km"] or area,
        "data_integrity": {
            "status": "validated_source_response",
            "is_official_census": False,
            "is_live_headcount": False,
        },
    }


@app.get("/api/v1/population/history/{area_id}")
def history(area_id: str):
    return {
        "area_id": area_id,
        "records": [],
        "message": "Historical series will be available after official historical boundary and population datasets are imported.",
    }


def report(location, pop, area, year, kind):
    density = round(pop / area, 2) if area else 0
    if kind == "csv":
        stream = io.StringIO()
        writer = csv.writer(stream)
        writer.writerow(["location", "population_estimate", "area_sq_km", "density_per_sq_km", "reference_year", "source"])
        writer.writerow([location, pop, area, density, year, "WorldPop Global2"])
        return Response(
            stream.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=poupscan.csv"},
        )
    buffer = io.BytesIO()
    from reportlab.pdfgen import canvas
    pdf = canvas.Canvas(buffer)
    y = 790
    for line in [
        "Poupscan Population Report",
        f"Location: {location}",
        f"Estimated population: {pop}",
        f"Area (km2): {area}",
        f"Density: {density}",
        f"Reference year: {year}",
        "Source: WorldPop Global2, approximately 100 m gridded estimates.",
        "This is not an official census count or a live headcount.",
        "Citation: Bondarenko et al. (2025), DOI: 10.5258/SOTON/WP00839.",
    ]:
        pdf.drawString(50, y, line)
        y -= 28
    pdf.save()
    return Response(
        buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=poupscan.pdf"},
    )


@app.get("/api/v1/reports/csv")
def csv_report(location: str = "Selected area", population: int = 0, area: float = 0, year: int = 2026):
    return report(location, population, area, year, "csv")


@app.get("/api/v1/reports/pdf")
def pdf_report(location: str = "Selected area", population: int = 0, area: float = 0, year: int = 2026):
    return report(location, population, area, year, "pdf")
