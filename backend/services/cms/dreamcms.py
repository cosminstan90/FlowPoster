"""
DreamCMS publish adapter.

Publishes generated pages to a DreamCMS instance via its publisher API
at POST /api/publisher/receive.

Required cms_config keys:
    api_url          — full endpoint URL,
                       e.g. https://candvisam.ro/api/publisher/receive
    publisher_token  — value of CMS_PUBLISHER_TOKEN in the DreamCMS .env

Optional cms_config keys:
    category_slug    — default category slug for all posts
    default_status   — "DRAFT" (default) or "PUBLISHED"  (UPPERCASE for DreamCMS)
    post_type        — "ARTICLE" | "DREAM_INTERPRETATION" | "SYMBOL"
                       defaults to "ARTICLE" (safe for general content)
    vertical_type    — "DREAMS" | "SYMBOLS" | "ANGEL_NUMBERS" | "GENERIC"
                       defaults to "GENERIC" (safe for general content)
    template_type    — "ARTICLE" | "DREAM" | "SYMBOL" | "HUB" | "GUIDE" | "LANDING"
                       defaults to "ARTICLE"

Payload contract (from DreamCMS app/api/publisher/receive/route.ts):
    title            string   required
    slug             string   required
    contentHtml      string   required  (camelCase)
    metaDescription  string?  (camelCase)
    metaTitle        string?  (camelCase)
    focusKeyword     string?  (camelCase)
    faqItems         [{question, answer}]?  (camelCase)
    featuredImageUrl  string?  (camelCase)
    status           "PUBLISHED" | "DRAFT"   (UPPERCASE — different from VelocityCMS)
    postType         "ARTICLE" | "DREAM_INTERPRETATION" | "SYMBOL"
    pageType         "CONTENT" | "LANDING" | "HUB" | "SUPPORT"  (optional)
    templateType     "ARTICLE" | "DREAM" | "SYMBOL" | ...  (optional, camelCase)
    verticalType     "DREAMS" | "SYMBOLS" | "ANGEL_NUMBERS" | "GENERIC"  (camelCase)
    categorySlug     string?  (camelCase)
    publisherPageId  string?  (camelCase, for idempotent upserts)
    publisherCampaign string? (camelCase)

    Note: DreamCMS generates its own GEO score and JSON-LD schema server-side,
    so geoScore/schemaMarkup are NOT sent — DreamCMS ignores them anyway.

Response: { success, postId, url, revalidated }
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


class DreamCMSAdapter(PublishAdapter):
    def __init__(self, config: dict) -> None:
        self._url = config["api_url"].rstrip("/")
        self._token = config["publisher_token"]
        self._category_slug: str | None = config.get("category_slug")
        # DreamCMS uses UPPERCASE status values
        self._default_status: str = config.get("default_status", "DRAFT").upper()
        self._post_type: str = config.get("post_type", "ARTICLE")
        self._vertical_type: str = config.get("vertical_type", "GENERIC")
        self._template_type: str = config.get("template_type", "ARTICLE")

        self._headers = {
            "X-CMS-Token": self._token,
            "Content-Type": "application/json",
        }

    # ---------------------------------------------------------------- publish

    async def publish(self, page: GeneratedPage) -> PublishResult:
        payload: dict = {
            # ── Required ────────────────────────────────────────────────────
            "title": page.title or "",
            "slug": page.slug or "",
            "contentHtml": page.content_html or "",
            # ── Optional content ────────────────────────────────────────────
            "metaDescription": page.meta_description or None,
            "faqItems": page.faq_items or [],
            "featuredImageUrl": page.featured_image_url or None,
            # ── Content classification ──────────────────────────────────────
            "postType": self._post_type,
            "verticalType": self._vertical_type,
            "templateType": self._template_type,
            # ── Publishing control ──────────────────────────────────────────
            "status": self._default_status,          # "DRAFT" | "PUBLISHED"
            "publisherPageId": str(page.id),         # enables idempotent upsert
        }

        # Optional category
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
        # Re-publish as DRAFT to revert the post (DreamCMS supports upsert via publisherPageId)
        payload = {
            "title": page.title or "",
            "slug": page.slug or "",
            "contentHtml": page.content_html or "",
            "status": "DRAFT",
            "publisherPageId": str(page.id),
            "postType": self._post_type,
            "verticalType": self._vertical_type,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(self._url, json=payload, headers=self._headers)
            resp.raise_for_status()
        return UnpublishResult(success=True)

    # ---------------------------------------------------------- test_connection

    async def test_connection(self) -> ConnectionResult:
        # DreamCMS has a dedicated /api/publisher/test endpoint that just
        # validates the token and returns { ok: true }
        test_url = self._url.replace("/receive", "/test")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(test_url, json={}, headers=self._headers)
                if resp.status_code == 200:
                    return ConnectionResult(
                        success=True, message="DreamCMS connection OK"
                    )
                # Fall back to trying the receive endpoint with a minimal payload
                resp2 = await client.post(
                    self._url, json={"title": "", "slug": ""}, headers=self._headers
                )
                if resp2.status_code in (200, 201, 400, 422):
                    return ConnectionResult(
                        success=True,
                        message=f"DreamCMS connection OK (HTTP {resp2.status_code})",
                    )
                resp2.raise_for_status()
                return ConnectionResult(success=True, message="DreamCMS connection OK")
        except httpx.HTTPStatusError as exc:
            return ConnectionResult(
                success=False,
                message=f"HTTP {exc.response.status_code}: {exc.response.text[:200]}",
            )
        except Exception as exc:
            return ConnectionResult(success=False, message=str(exc))
