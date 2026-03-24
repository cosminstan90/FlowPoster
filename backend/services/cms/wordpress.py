"""
WordPress REST API publish adapter.

Required cms_config keys:
    url          — site root, e.g. https://example.com
    username     — WP username
    app_password — Application Password (no spaces)
"""
from __future__ import annotations

import base64
import mimetypes

import httpx

from backend.models.generated_page import GeneratedPage
from backend.services.cms.base_adapter import (
    ConnectionResult,
    PublishAdapter,
    PublishResult,
    UnpublishResult,
)


class WordPressAdapter(PublishAdapter):
    def __init__(self, config: dict) -> None:
        self._base = config["url"].rstrip("/")
        credentials = f"{config['username']}:{config['app_password']}"
        token = base64.b64encode(credentials.encode()).decode()
        self._headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
        }

    # ---------------------------------------------------------------- helpers

    def _api(self, path: str) -> str:
        return f"{self._base}/wp-json/wp/v2/{path.lstrip('/')}"

    async def _upload_image(self, client: httpx.AsyncClient, image_url: str) -> int | None:
        """Download image from URL and upload to WP Media Library. Returns media ID."""
        try:
            img_resp = await client.get(image_url, timeout=15, follow_redirects=True)
            img_resp.raise_for_status()
            content_type = img_resp.headers.get("content-type", "image/jpeg").split(";")[0]
            ext = mimetypes.guess_extension(content_type) or ".jpg"
            filename = f"featured{ext}"

            upload_headers = {
                "Authorization": self._headers["Authorization"],
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": content_type,
            }
            media_resp = await client.post(
                self._api("media"),
                content=img_resp.content,
                headers=upload_headers,
                timeout=30,
            )
            media_resp.raise_for_status()
            return media_resp.json().get("id")
        except Exception:
            return None

    # ---------------------------------------------------------------- adapter

    async def publish(self, page: GeneratedPage) -> PublishResult:
        async with httpx.AsyncClient(timeout=20) as client:
            featured_media_id: int | None = None
            if page.featured_image_url:
                featured_media_id = await self._upload_image(client, page.featured_image_url)

            body: dict = {
                "title": page.title or "",
                "content": page.content_html or "",
                "slug": page.slug or "",
                "status": "publish",
                "excerpt": page.meta_description or "",
                "meta": {
                    "_yoast_wpseo_title": page.title or "",
                    "_yoast_wpseo_metadesc": page.meta_description or "",
                },
                "categories": [],
                "tags": [],
            }
            if featured_media_id:
                body["featured_media"] = featured_media_id

            resp = await client.post(
                self._api("posts"),
                json=body,
                headers=self._headers,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return PublishResult(
                success=True,
                published_url=data.get("link", ""),
                remote_id=str(data.get("id", "")),
            )

    async def unpublish(self, page: GeneratedPage) -> UnpublishResult:
        if not page.published_url:
            return UnpublishResult(success=False)

        # Extract remote_id stored in published_url or fall back to slug lookup
        remote_id = await self._resolve_remote_id(page)
        if not remote_id:
            return UnpublishResult(success=False)

        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.patch(
                self._api(f"posts/{remote_id}"),
                json={"status": "draft"},
                headers=self._headers,
            )
            resp.raise_for_status()
        return UnpublishResult(success=True)

    async def test_connection(self) -> ConnectionResult:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    self._api("users/me"),
                    headers=self._headers,
                )
                resp.raise_for_status()
                name = resp.json().get("name", "unknown")
                return ConnectionResult(success=True, message=f"Connected as '{name}'")
        except httpx.HTTPStatusError as exc:
            return ConnectionResult(success=False, message=f"HTTP {exc.response.status_code}")
        except Exception as exc:
            return ConnectionResult(success=False, message=str(exc))

    async def _resolve_remote_id(self, page: GeneratedPage) -> str | None:
        """Look up WP post ID by slug."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    self._api("posts"),
                    params={"slug": page.slug, "per_page": 1},
                    headers=self._headers,
                )
                resp.raise_for_status()
                results = resp.json()
                if results:
                    return str(results[0]["id"])
        except Exception:
            pass
        return None
