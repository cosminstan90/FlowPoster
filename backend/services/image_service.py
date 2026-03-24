"""
Unsplash image search service.
Returns {url, credit, photographer} or None when key is not configured.
"""
from __future__ import annotations

import httpx

from backend.config import settings

UNSPLASH_API = "https://api.unsplash.com/search/photos"


async def search(keyword: str) -> dict | None:
    """
    Search Unsplash for a relevant landscape photo.

    Returns::

        {"url": str, "credit": str, "photographer": str}

    or ``None`` if no key is configured or no results are found.
    """
    if not settings.UNSPLASH_ACCESS_KEY:
        return None

    params = {
        "query": keyword,
        "per_page": 1,
        "orientation": "landscape",
        "content_filter": "high",
    }
    headers = {"Authorization": f"Client-ID {settings.UNSPLASH_ACCESS_KEY}"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(UNSPLASH_API, params=params, headers=headers)
            resp.raise_for_status()
            results = resp.json().get("results", [])
            if not results:
                return None

            photo = results[0]
            url = photo["urls"].get("regular") or photo["urls"].get("full")
            photographer = photo.get("user", {}).get("name", "Unknown")
            return {
                "url": url,
                "credit": f"Photo by {photographer} on Unsplash",
                "photographer": photographer,
            }
    except Exception:
        return None
