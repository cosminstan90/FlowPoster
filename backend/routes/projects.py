import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.deps import CurrentUser, DB
from backend.models import Campaign, GeneratedPage, Keyword, Project, SiteContext
from backend.schemas.common import APIResponse
from backend.schemas.project import (
    ProjectCreate,
    ProjectDetail,
    ProjectOut,
    ProjectStats,
    ProjectUpdate,
    ProjectWithStats,
)
from backend.schemas.site_context import SiteContextOut

router = APIRouter(prefix="/projects", tags=["projects"])


def _build_stats_query():
    now = datetime.now(timezone.utc)
    return (
        select(
            Project,
            func.count(Keyword.id.distinct()).label("total_keywords"),
            func.count(
                case((GeneratedPage.status == "published", GeneratedPage.id))
            ).label("total_pages_published"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            (extract("year", GeneratedPage.created_at) == now.year)
                            & (extract("month", GeneratedPage.created_at) == now.month),
                            GeneratedPage.cost_usd,
                        )
                    )
                ),
                0,
            ).label("cost_this_month"),
        )
        .outerjoin(Campaign, Campaign.project_id == Project.id)
        .outerjoin(Keyword, Keyword.campaign_id == Campaign.id)
        .outerjoin(GeneratedPage, GeneratedPage.keyword_id == Keyword.id)
        .group_by(Project.id)
        .order_by(Project.created_at.desc())
    )


def _row_to_project_with_stats(row) -> ProjectWithStats:
    out = ProjectWithStats.model_validate(row.Project)
    out.stats = ProjectStats(
        total_keywords=row.total_keywords or 0,
        total_pages_published=row.total_pages_published or 0,
        cost_this_month=Decimal(str(row.cost_this_month or 0)),
    )
    return out


@router.get("", response_model=APIResponse[list[ProjectWithStats]])
async def list_projects(
    _: str = CurrentUser,
    db: AsyncSession = DB,
):
    result = await db.execute(_build_stats_query())
    rows = result.all()
    projects = [_row_to_project_with_stats(r) for r in rows]
    return APIResponse.ok(data=projects, message=f"{len(projects)} projects")


@router.post("", response_model=APIResponse[ProjectOut], status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    _: str = CurrentUser,
    db: AsyncSession = DB,
):
    project = Project(**body.model_dump())
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return APIResponse.ok(data=ProjectOut.model_validate(project), message="Project created")


@router.get("/{project_id}", response_model=APIResponse[ProjectDetail])
async def get_project(
    project_id: uuid.UUID,
    _: str = CurrentUser,
    db: AsyncSession = DB,
):
    # Stats row
    result = await db.execute(_build_stats_query().where(Project.id == project_id))
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")

    with_stats = _row_to_project_with_stats(row)

    # Site context
    sc_result = await db.execute(
        select(SiteContext).where(SiteContext.project_id == project_id)
    )
    sc = sc_result.scalar_one_or_none()

    detail = ProjectDetail(
        **with_stats.model_dump(),
        site_context=SiteContextOut.model_validate(sc) if sc else None,
    )
    return APIResponse.ok(data=detail, message="OK")


@router.put("/{project_id}", response_model=APIResponse[ProjectOut])
async def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdate,
    _: str = CurrentUser,
    db: AsyncSession = DB,
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    await db.flush()
    await db.refresh(project)
    return APIResponse.ok(data=ProjectOut.model_validate(project), message="Project updated")


@router.delete("/{project_id}", response_model=APIResponse[None])
async def delete_project(
    project_id: uuid.UUID,
    _: str = CurrentUser,
    db: AsyncSession = DB,
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    campaign_count = await db.scalar(
        select(func.count(Campaign.id)).where(Campaign.project_id == project_id)
    )
    if campaign_count:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete project with {campaign_count} existing campaign(s)",
        )

    await db.delete(project)
    return APIResponse.ok(data=None, message="Project deleted")
