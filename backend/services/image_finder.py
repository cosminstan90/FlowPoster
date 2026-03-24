"""
Unsplash image search integration.
If UNSPLASH_ACCESS_KEY is not configured, returns None gracefully.
"""
from __future__ import annotations

import httpx

from backend.config import settings

UNSPLASH_API = "https://api.unsplash.com/search/photos"


async def find_image(query: str) -> dict | None:
    """
    Search Unsplash for a relevant image.
    Returns {"url": str, "credit": str} or None.
    """
    if not settings.UNSPLASH_ACCESS_KEY:
        return None

    params = {
        "query": query,
        "per_page": 1,
        "orientation": "landscape",
        "content_filter": "high",
    }
    headers = {"Authorization": f"Client-ID {settings.UNSPLASH_ACCESS_KEY}"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(UNSPLASH_API, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            if not results:
                return None
            photo = results[0]
            url = photo["urls"].get("regular") or photo["urls"].get("full")
            photographer = photo.get("user", {}).get("name", "Unsplash")
            return {"url": url, "credit": f"Photo by {photographer} on Unsplash"}
    except Exception:
        return None
