"""
VelocityCMS publish adapter.

Publishes generated pages to a VelocityCMS instance via its publisher API
at POST /api/publisher/receive.

Required cms_config keys:
    api_url          — full endpoint URL,
                       e.g. https://divet.ro/api/publisher/receive
    publisher_token  — value of CMS_PUBLISHER_TOKEN in the VelocityCMS .env
    site_id          — the Site.id UUID from VelocityCMS (required by the API)

Optional cms_config keys:
    category_slug    — default category slug for all posts (can be overridden
                       per-page via keyword.category_slug if that field exists)
    default_status   — "draft" (default) or "published"

Payload contract (from VelocityCMS app/api/publisher/receive/route.ts):
    title            string   required
    slug             string   required
    contentHtml      string   required
    siteId           string   required
    metaDescription  string?
    schemaMarkup     object?  (VelocityCMS also generates its own — providing it
                               skips the server-side generation for a small speedup)
    faqItems         [{question, answer}]?
    focusKeyword     string?
    categorySlug     string?
    status           "draft" | "published"   (lowercase)
    publisherPageId  string?  (used for idempotent upserts — pass page.id)
    publisherCampaign string?
    featuredImageUrl  string?
    featuredImageCredit string?
    model            string?  (model name used to generate the content)
    geoScore         number?  (skip server-side GEO calculation if provided)
    geoBreakdown     object?
    directAnswer     string?
    speakableSections string[]?

Response: { success, postId, url, scheduledAt, revalidated }
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
        self._token = config["publisher_token"]
        self._site_id: str = config["site_id"]
        self._category_slug: str | None = config.get("category_slug")
        self._default_status: str = config.get("default_status", "draft")

        self._headers = {
            "x-cms-token": self._token,
            "Content-Type": "application/json",
        }

    # ---------------------------------------------------------------- publish

    async def publish(self, page: GeneratedPage) -> PublishResult:
        payload: dict = {
            # ── Required ────────────────────────────────────────────────────
            "siteId": self._site_id,
            "title": page.title or "",
            "slug": page.slug or "",
            "contentHtml": page.content_html or "",
            # ── Optional content ────────────────────────────────────────────
            "metaDescription": page.meta_description or None,
            "faqItems": page.faq_items or [],
            "featuredImageUrl": page.featured_image_url or None,
            "featuredImageCredit": page.featured_image_credit or None,
            # ── Publishing control ──────────────────────────────────────────
            "status": self._default_status,          # "draft" | "published"
            "publisherPageId": str(page.id),         # enables idempotent upsert
            # ── GEO data (skip server-side calculation if we pass scores) ───
            "geoScore": page.geo_score,
            "geoBreakdown": page.geo_breakdown,
            "speakableSections": page.speakable_sections or [],
            # ── Schema / SEO ────────────────────────────────────────────────
            "schemaMarkup": page.schema_markup,
            # ── Metadata ────────────────────────────────────────────────────
            "model": page.model_used,
        }

        # Optional category override
        if self._category_slug:
            payload["categorySlug"] = self._category_slug

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(self._url, json=payload, headers=self._headers)
            resp.raise_for_status()
            data = resp.json()
            return PublishResult(
                success=data.get("success", True),
                published_url=data.get("url", ""),
                remote_id=str(data.get("postId", "")),
            )

    # --------------------------------------------------------------- unpublish

    async def unpublish(self, page: GeneratedPage) -> UnpublishResult:
        # VelocityCMS does not have a dedicated unpublish endpoint.
        # Re-publish with status=draft to revert the post.
        payload = {
            "siteId": self._site_id,
            "title": page.title or "",
            "slug": page.slug or "",
            "contentHtml": page.content_html or "",
            "status": "draft",
            "publisherPageId": str(page.id),
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self._url, json=payload, headers=self._headers)
            resp.raise_for_status()
        return UnpublishResult(success=True)

    # ---------------------------------------------------------- test_connection

    async def test_connection(self) -> ConnectionResult:
        # Hit the receive endpoint with a minimal payload that will be rejected
        # cleanly (missing required fields) — a 400 means auth passed, which is
        # all we need to confirm connectivity + token validity.
        test_payload = {"siteId": self._site_id}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    self._url, json=test_payload, headers=self._headers
                )
                if resp.status_code in (200, 201, 400, 422):
                    # 400/422 = auth OK, payload rejected as expected
                    return ConnectionResult(
                        success=True,
                        message=f"VelocityCMS connection OK (HTTP {resp.status_code})",
                    )
                resp.raise_for_status()
                return ConnectionResult(success=True, message="VelocityCMS connection OK")
        except httpx.HTTPStatusError as exc:
            return ConnectionResult(
                success=False,
                message=f"HTTP {exc.response.status_code}: {exc.response.text[:200]}",
            )
        except Exception as exc:
            return ConnectionResult(success=False, message=str(exc))
