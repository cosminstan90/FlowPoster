"""
Generic PHP custom endpoint publish adapter.

Required cms_config keys:
    endpoint_url  — URL that accepts POST requests
    secret_token  — passed as X-SEO-Token header
"""
from __future__ import annotations

import httpx

from backend.models.generated_page import GeneratedPage
from backend.services.cms.base_adapter import (
    ConnectionResult,
    PublishAdapter,
    PublishResult,
    UnpublishResult,
)


class PHPCustomAdapter(PublishAdapter):
    def __init__(self, config: dict) -> None:
        self._url = config["endpoint_url"].rstrip("/")
        self._headers = {
            "X-SEO-Token": config["secret_token"],
            "Content-Type": "application/json",
        }

    async def publish(self, page: GeneratedPage) -> PublishResult:
        payload = {
            "action": "publish",
            "title": page.title or "",
            "slug": page.slug or "",
            "content_html": page.content_html or "",
            "meta_description": page.meta_description or "",
            "schema_markup": page.schema_markup,
            "faq_items": page.faq_items or [],
            "featured_image_url": page.featured_image_url,
            "featured_image_credit": page.featured_image_credit,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self._url, json=payload, headers=self._headers)
            resp.raise_for_status()
            data = resp.json()
            return PublishResult(
                success=data.get("success", True),
                published_url=data.get("url", ""),
                remote_id=str(data.get("id", "")),
            )

    async def unpublish(self, page: GeneratedPage) -> UnpublishResult:
        payload = {
            "action": "unpublish",
            "remote_id": page.published_url or page.slug or "",
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(self._url, json=payload, headers=self._headers)
            resp.raise_for_status()
        return UnpublishResult(success=True)

    async def test_connection(self) -> ConnectionResult:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    self._url,
                    json={"action": "test"},
                    headers=self._headers,
                )
                resp.raise_for_status()
                data = resp.json()
                return ConnectionResult(
                    success=data.get("success", True),
                    message=data.get("message", "Connection OK"),
                )
        except httpx.HTTPStatusError as exc:
            return ConnectionResult(success=False, message=f"HTTP {exc.response.status_code}")
        except Exception as exc:
            return ConnectionResult(success=False, message=str(exc))
