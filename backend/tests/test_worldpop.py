import asyncio
import pytest
from app.services import worldpop


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "total_population": 1234.56,
            "area_km2": 10.0,
            "population_density": 123.456,
            "data_year": 2026,
            "data_source": "WorldPop Global2 R2025A, 100 m",
        }


class FakeClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, *args, **kwargs):
        return FakeResponse()


def test_worldpop_response_is_validated(monkeypatch):
    monkeypatch.setattr(worldpop.httpx, "AsyncClient", FakeClient)
    result = asyncio.run(worldpop.estimate(
        {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
        2026,
    ))
    assert result["estimated_population"] == 1235
    assert result["reference_year"] == 2026
    assert result["estimate_type"] == "modelled gridded population estimate"


def test_worldpop_rejects_unrecognised_schema(monkeypatch):
    class BadResponse(FakeResponse):
        def json(self):
            return {"population": 1234}

    class BadClient(FakeClient):
        async def post(self, *args, **kwargs):
            return BadResponse()

    monkeypatch.setattr(worldpop.httpx, "AsyncClient", BadClient)
    with pytest.raises(worldpop.WorldPopUnavailable):
        asyncio.run(worldpop.estimate({"type": "Polygon", "coordinates": []}, 2026))
