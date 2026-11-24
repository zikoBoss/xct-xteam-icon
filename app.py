"""xct-xteam-icon — icon proxy API (XCT team).

GET /<icon_name>.png  ->  fetches the icon from the upstream icon CDN
                            (URL kept in the ICON_BASE_URL env var, never
                            exposed in the public link) and returns it as PNG.

The upstream URL is configured only via the ICON_BASE_URL environment
variable (set in Vercel project settings), so the public repo and the
public links never reveal where the icons actually come from.
"""

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


@app.get("/")
def home():
    return {"status": "API running", "usage": "/<icon_name>.png"}


@app.get("/{icon_name}.png")
async def get_icon(icon_name: str):
    if not ICON_BASE_URL:
        return JSONResponse(
            {"error": "ICON_BASE_URL not configured"}, status_code=500
        )

    if not NAME_RE.match(icon_name):
        return JSONResponse({"error": "invalid icon name"}, status_code=400)

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
