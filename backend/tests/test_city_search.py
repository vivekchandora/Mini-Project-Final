from fastapi.testclient import TestClient
import app.main as main


def test_city_search_ranks_polygon_boundaries_first(monkeypatch):
    calls = {"count": 0}

    async def fake_get_json(path, params):
        calls["count"] += 1
        if params.get("featureType") == "city":
            return [{
                "display_name": "Pune, Maharashtra, India",
                "lat": "18.52", "lon": "73.85", "osm_id": 10, "osm_type": "node",
                "category": "place", "type": "city", "addresstype": "city",
                "importance": 0.8,
            }]
        return [
            {
                "display_name": "Pune Municipal Boundary, Maharashtra, India",
                "lat": "18.52", "lon": "73.85", "osm_id": 20, "osm_type": "relation",
                "category": "boundary", "type": "administrative", "addresstype": "city",
                "importance": 0.7,
                "geojson": {"type": "Polygon", "coordinates": [[[73, 18], [74, 18], [74, 19], [73, 18]]]},
                "extratags": {"boundary": "administrative"},
            }
        ]

    monkeypatch.setattr(main, "get_json", fake_get_json)
    client = TestClient(main.app)
    response = client.get("/api/v1/locations/search?q=Pune")
    assert response.status_code == 200
    results = response.json()
    assert results[0]["osm_id"] == 20
    assert results[0]["has_boundary"] is True
    assert results[-1]["has_boundary"] is False
    assert calls["count"] == 2
