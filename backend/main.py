from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from backend.database import AsyncSessionLocal
from backend.routes.auth import router as auth_router
from backend.routes.campaigns import router as campaigns_router
from backend.routes.costs import router as costs_router
from backend.routes.generation import router as generation_router
from backend.routes.keywords import router as keywords_router
from backend.routes.pages import router as pages_router
from backend.routes.projects import router as projects_router
from backend.routes.publish import router as publish_router
from backend.routes.site_context import router as site_context_router
from backend.routes.templates import router as templates_router
from backend.services.template_seeder import seed_default_templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncSessionLocal() as db:
        await seed_default_templates(db)
    yield


app = FastAPI(title="SEO Publisher", version="0.1.0", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(site_context_router)
app.include_router(campaigns_router)
app.include_router(keywords_router)
app.include_router(generation_router)
app.include_router(costs_router)
app.include_router(pages_router)
app.include_router(publish_router)
app.include_router(templates_router)


@app.get("/health", tags=["health"])
async def health():
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception:
        return {"status": "ok", "db": "disconnected"}
