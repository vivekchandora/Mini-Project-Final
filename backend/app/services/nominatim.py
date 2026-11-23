"""Small shared Nominatim client with a conservative one-request-per-second limit."""
import asyncio
import os
import time
import httpx

BASE = os.getenv("NOMINATIM_BASE_URL", "https://nominatim.openstreetmap.org").rstrip("/")
USER_AGENT = os.getenv(
    "GEOCODING_USER_AGENT",
    "PopScan/1.2 (India population research application; configure a contact email)",
)
CONTACT_EMAIL = os.getenv("GEOCODING_CONTACT_EMAIL", "").strip()
_lock = asyncio.Lock()
_last_request = 0.0


async def get_json(path: str, params: dict):
    global _last_request
    async with _lock:
        delay = 1.05 - (time.monotonic() - _last_request)
        if delay > 0:
            await asyncio.sleep(delay)
        async with httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        ) as client:
            request_params = dict(params)
            if CONTACT_EMAIL:
                request_params.setdefault("email", CONTACT_EMAIL)
            response = await client.get(f"{BASE}/{path.lstrip('/')}", params=request_params)
            _last_request = time.monotonic()
            response.raise_for_status()
            return response.json()
