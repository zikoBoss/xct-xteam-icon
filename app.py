"""xct-xteam-icon — icon proxy API (XCT team).

GET /<icon_name>.png   ->  icon by its name (e.g. Icon_Pet_Golden_Panther)
GET /item/<item_id>.png ->  icon by the item's numeric id (e.g. 1310000024)

Both fetch the icon from the upstream icon CDN (URL kept in the
ICON_BASE_URL env var, never exposed in the public link) and return it
as PNG. The item-id route resolves the id to an icon name through the
local icon_map.json (itemID -> icon name), so no other service is needed.
"""

import json
import os
import re

import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response

app = FastAPI()

ICON_BASE_URL = os.environ.get("ICON_BASE_URL", "").rstrip("/")

# Icon names look like Icon_Pet_Golden_Panther / Icon_M1887_Element_Thunder:
# letters, digits, underscore, hyphen only. Anything else is rejected
# before we ever build an upstream URL (no path traversal, no "..").
NAME_RE = re.compile(r"^[A-Za-z0-9_\-]+$")

_MAP_PATH = os.path.join(os.path.dirname(__file__), "icon_map.json")
_icon_map = None
_map_failed = False


def _icon_name_for(item_id: str):
    """Resolve a numeric item id to its icon name, or None if unknown."""
    global _icon_map, _map_failed
    if _icon_map is None and not _map_failed:
        try:
            with open(_MAP_PATH, "r", encoding="utf-8") as f:
                _icon_map = json.load(f)
        except Exception:
            _map_failed = True
            return None
    if _icon_map is None:
        return None
    return _icon_map.get(str(item_id))


async def _fetch_icon(icon_name: str):
    """Fetch one icon from upstream. Returns a FastAPI response."""
    url = f"{ICON_BASE_URL}/{icon_name}.png"
    try:
        async with httpx.AsyncClient(
            timeout=15.0, headers={"User-Agent": "xct-xteam-icon/1.0"}
        ) as client:
            r = await client.get(url)
    except httpx.RequestError:
        return JSONResponse({"error": "upstream fetch failed"}, status_code=502)

    # Upstream answers 403 AccessDenied (S3-style) for a missing icon,
    # and 404 for some others: both mean "this icon does not exist".
    if r.status_code in (403, 404):
        return JSONResponse({"error": "icon not found"}, status_code=404)
    if r.status_code != 200:
        return JSONResponse({"error": "upstream error"}, status_code=502)

    # Icons never change content under the same name: cacheable for a day.
    # Errors above are never cached (no Cache-Control header on them).
    return Response(
        content=r.content,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.get("/")
def home():
    return {
        "status": "API running",
        "usage": "/<icon_name>.png or /item/<item_id>.png",
    }


@app.get("/item/{item_id}.png")
async def get_icon_by_id(item_id: str):
    if not ICON_BASE_URL:
        return JSONResponse(
            {"error": "ICON_BASE_URL not configured"}, status_code=500
        )

    if not item_id.isdigit():
        return JSONResponse({"error": "invalid item id"}, status_code=400)

    icon_name = _icon_name_for(item_id)
    if not icon_name:
        return JSONResponse({"error": "item not found"}, status_code=404)

    return await _fetch_icon(icon_name)


@app.get("/{icon_name}.png")
async def get_icon(icon_name: str):
    if not ICON_BASE_URL:
        return JSONResponse(
            {"error": "ICON_BASE_URL not configured"}, status_code=500
        )

    if not NAME_RE.match(icon_name):
        return JSONResponse({"error": "invalid icon name"}, status_code=400)

    return await _fetch_icon(icon_name)
