import re
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from backend.deps import CurrentUser, DB
from backend.models import Project, SiteContext
from backend.schemas.common import APIResponse
from backend.schemas.site_context import SiteContextOut, SiteContextUpsert
from backend.services.ai import prompts
from backend.services.ai.client_factory import get_fast_client

router = APIRouter(prefix="/projects/{project_id}/context", tags=["site-context"])


class AnalyzeSiteRequest(BaseModel):
    site_url: str | None = None  # overrides project domain if provided


class SiteContextSuggestion(BaseModel):
    niche: str
    target_audience: str
    tone: str
    topics_to_avoid: str | None


def _strip_html(html: str) -> str:
    text = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.DOTALL)
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_sitemap_urls(xml: str) -> list[str]:
    return re.findall(r"<loc>\s*(https?://[^\s<]+)\s*</loc>", xml)


async def _require_project(project_id: uuid.UUID, db: AsyncSession) -> None:
    exists = await db.scalar(select(Project.id).where(Project.id == project_id))
    if not exists:
        raise HTTPException(status_code=404, detail="Project not found")


@router.get("", response_model=APIResponse[SiteContextOut])
async def get_context(
    project_id: uuid.UUID,
    _: CurrentUser,
    db: DB,
):
    await _require_project(project_id, db)
    result = await db.execute(
        select(SiteContext).where(SiteContext.project_id == project_id)
    )
    sc = result.scalar_one_or_none()
    if not sc:
        raise HTTPException(status_code=404, detail="Site context not found")
    return APIResponse.ok(data=SiteContextOut.model_validate(sc), message="OK")


@router.put("", response_model=APIResponse[SiteContextOut])
async def upsert_context(
    project_id: uuid.UUID,
    body: SiteContextUpsert,
    _: CurrentUser,
    db: DB,
):
    await _require_project(project_id, db)

    result = await db.execute(
        select(SiteContext).where(SiteContext.project_id == project_id)
    )
    sc = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if sc is None:
        sc = SiteContext(project_id=project_id, updated_at=now, **body.model_dump())
        db.add(sc)
        created = True
    else:
        for field, value in body.model_dump().items():
            setattr(sc, field, value)
        sc.updated_at = now
        created = False

    await db.flush()
    await db.refresh(sc)
    msg = "Site context created" if created else "Site context updated"
    return APIResponse.ok(data=SiteContextOut.model_validate(sc), message=msg)


@router.post("/analyze", response_model=APIResponse[SiteContextSuggestion])
async def analyze_site(
    project_id: uuid.UUID,
    body: AnalyzeSiteRequest,
    _: CurrentUser,
    db: DB,
):
    """Fetch the site homepage + sitemap and use AI to suggest site context fields."""
    project = await db.scalar(select(Project).where(Project.id == project_id))
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    base_url = body.site_url or f"https://{project.domain}"
    base_url = base_url.rstrip("/")

    homepage_text = ""
    sitemap_urls: list[str] = []

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        # 1. Fetch homepage
        try:
            resp = await client.get(base_url)
            homepage_text = _strip_html(resp.text)[:5000]
        except Exception:
            raise HTTPException(status_code=422, detail=f"Could not fetch {base_url}")

        # 2. Try common sitemap locations
        for path in ("/sitemap.xml", "/sitemap_index.xml", "/sitemap"):
            try:
                s = await client.get(f"{base_url}{path}")
                if s.status_code == 200 and "<loc>" in s.text:
                    sitemap_urls = _extract_sitemap_urls(s.text)[:30]
                    break
            except Exception:
                continue

    # 3. Call AI
    import json
    client_ai = get_fast_client("claude-sonnet-4-6")
    sys_p, usr_p = prompts.site_analyzer(
        domain=project.domain,
        homepage_text=homepage_text,
        sitemap_sample=sitemap_urls,
    )
    result = await client_ai.call(sys_p, usr_p, max_tokens=512)

    try:
        cleaned = result.text.strip()
        m = __import__("re").search(r"```(?:json)?\s*\n?(.*?)```", cleaned, __import__("re").DOTALL)
        if m:
            cleaned = m.group(1).strip()
        data = json.loads(cleaned)
    except Exception:
        raise HTTPException(status_code=500, detail="AI returned invalid JSON")

    suggestion = SiteContextSuggestion(
        niche=data.get("niche", ""),
        target_audience=data.get("target_audience", ""),
        tone=data.get("tone", "professional"),
        topics_to_avoid=data.get("topics_to_avoid"),
    )
    return APIResponse.ok(data=suggestion, message="Analysis complete")
