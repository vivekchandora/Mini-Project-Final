from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
def test_health(): assert c.get("/health").json()["status"]=="ok"
def test_invalid_polygon():
 r=c.post("/api/v1/population/custom-area",json={"geojson":{"type":"Point","coordinates":[1,2]}})
 assert r.status_code==422
def test_polygon_request_fails_closed_or_returns_source_result():
 r=c.post("/api/v1/population/custom-area",json={"geojson":{"type":"Polygon","coordinates":[[[77,28],[77.01,28],[77.01,28.01],[77,28.01],[77,28]]]}})
 assert r.status_code in (200,503)
 if r.status_code==503: assert r.json()["detail"]["estimated_population"] is None
def test_csv_export():
 r=c.get("/api/v1/reports/csv?location=Test&population=100&area=2")
 assert r.status_code==200 and "population" in r.text
def test_pdf_export():
 r=c.get("/api/v1/reports/pdf?location=Test&population=100&area=2")
 assert r.status_code==200 and r.content.startswith(b"%PDF")



def test_place_search_endpoint_is_removed():
    assert c.get("/api/v1/locations/search?q=Pune").status_code == 404
    assert c.post("/api/v1/population/location", json={}).status_code == 404
