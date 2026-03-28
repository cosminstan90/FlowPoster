from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.deps import CurrentUser, DB
from backend.models import Campaign, Keyword
from backend.schemas.common import APIResponse
from backend.schemas.generation import (
    BulkEstimate,
    BulkGenerateRequest,
    BulkGenerateResult,
    GeneratedPageOut,
)
from backend.services.ai.pipeline import run_pipeline
from backend.services.cost_calculator import estimate_bulk_cost
from backend.worker.queue import get_arq_pool

router = APIRouter(prefix="/generate", tags=["generation"])


@router.post(
    "/{keyword_id}",
    response_model=APIResponse[GeneratedPageOut],
    status_code=status.HTTP_201_CREATED,
)
async def generate_single(
    keyword_id: uuid.UUID,
    _: CurrentUser,
    db: DB,
):
    """Run the full AI generation pipeline for one keyword (synchronous)."""
    kw = await db.scalar(select(Keyword).where(Keyword.id == keyword_id))
    if not kw:
        raise HTTPException(status_code=404, detail="Keyword not found")

    if kw.status not in ("pending", "error"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Keyword status is '{kw.status}'; must be pending or error to generate",
        )

    try:
        page = await run_pipeline(keyword_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return APIResponse.ok(
        data=GeneratedPageOut.model_validate(page),
        message="Generation complete",
    )


@router.post(
    "/bulk",
    response_model=APIResponse[BulkGenerateResult],
)
async def generate_bulk(
    body: BulkGenerateRequest,
    _: CurrentUser,
    db: DB,
    confirm: bool = Query(False, description="Set to true to actually enqueue jobs"),
):
    """
    Bulk generation with cost gate.

    Without ``?confirm=true`` → returns the cost estimate only (HTTP 200).
    With ``?confirm=true``    → enqueues ARQ jobs (HTTP 202).
    """
    # Validate campaign
    campaign = await db.scalar(select(Campaign).where(Campaign.id == body.campaign_id))
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    # Validate keywords belong to the campaign and are eligible
    result = await db.execute(
        select(Keyword).where(
            Keyword.id.in_(body.keyword_ids),
            Keyword.campaign_id == body.campaign_id,
        )
    )
    keywords = result.scalars().all()
    eligible = [kw for kw in keywords if kw.status in ("pending", "error")]

    if not eligible:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No eligible keywords (must be pending or error status)",
        )

    # Build estimate
    model = campaign.model or "claude-sonnet-4-20250514"
    est_raw = estimate_bulk_cost(len(eligible), model)
    estimate = BulkEstimate(
        model=model,
        keyword_count=len(eligible),
        **est_raw,
    )

    if not confirm:
        # Dry-run: return estimate without enqueuing
        return APIResponse.ok(
            data=BulkGenerateResult(
                queued=0,
                keyword_ids=[kw.id for kw in eligible],
                estimate=estimate,
            ),
            message=(
                f"Estimate: {estimate.min_usd}–{estimate.max_usd} USD "
                f"for {len(eligible)} keywords. Add ?confirm=true to enqueue."
            ),
        )

    # --- confirmed: enqueue ---
    now_utc = datetime.now(timezone.utc)
    for kw in eligible:
        kw.status = "queued"
        kw.updated_at = now_utc
    await db.flush()

    redis = await get_arq_pool()
    try:
        for kw in eligible:
            await redis.enqueue_job("run_generation_pipeline", str(kw.id))
    finally:
        await redis.aclose()

    queued_ids = [kw.id for kw in eligible]
    return APIResponse(
        success=True,
        data=BulkGenerateResult(
            queued=len(queued_ids),
            keyword_ids=queued_ids,
            estimate=estimate,
        ),
        message=f"Enqueued {len(queued_ids)} keyword(s) for generation",
    )
