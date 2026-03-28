"""
VelocityCMS publish adapter.

Publishes generated pages to a VelocityCMS instance via its publisher API.

Required cms_config keys:
    api_url          — VelocityCMS publisher endpoint,
                       e.g. https://divet.ro/api/publisher/receive
    publisher_token  — Value of CMS_PUBLISHER_TOKEN in the VelocityCMS .env
    site_id          — (optional) target site ID; omit to use the default site
                       for the incoming domain
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


class VelocityCMSAdapter(PublishAdapter):
    def __init__(self, config: dict) -> None:
        self._url = config["api_url"].rstrip("/")
        self._headers = {
            "X-CMS-Token": config["publisher_token"],
            "Content-Type": "application/json",
        }
        self._site_id: str | None = config.get("site_id")

    # ---------------------------------------------------------------- helpers

    def _payload_base(self) -> dict:
        base: dict = {}
        if self._site_id:
            base["siteId"] = self._site_id
        return base

    # ---------------------------------------------------------------- publish

    async def publish(self, page: GeneratedPage) -> PublishResult:
        payload = {
            **self._payload_base(),
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

    # --------------------------------------------------------------- unpublish

    async def unpublish(self, page: GeneratedPage) -> UnpublishResult:
        payload = {
            **self._payload_base(),
            "action": "unpublish",
            "remote_id": page.publisher_page_id or page.slug or "",
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(self._url, json=payload, headers=self._headers)
            resp.raise_for_status()
        return UnpublishResult(success=True)

    # ---------------------------------------------------------- test_connection

    async def test_connection(self) -> ConnectionResult:
        try:
            payload = {**self._payload_base(), "action": "test"}
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(self._url, json=payload, headers=self._headers)
                resp.raise_for_status()
                data = resp.json()
                return ConnectionResult(
                    success=data.get("success", True),
                    message=data.get("message", "VelocityCMS connection OK"),
                )
        except httpx.HTTPStatusError as exc:
            return ConnectionResult(
                success=False,
                message=f"HTTP {exc.response.status_code}: {exc.response.text[:200]}",
            )
        except Exception as exc:
            return ConnectionResult(success=False, message=str(exc))
