from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class DailyBreakdown(BaseModel):
    date: str
    cost: Decimal
    pages: int


class ProjectCostOut(BaseModel):
    total_usd: Decimal
    pages_count: int
    tokens_input: int
    tokens_output: int
    budget_usd: Decimal
    budget_remaining: Decimal
    budget_percent_used: Decimal
    daily_breakdown: list[DailyBreakdown]


class CampaignCostOut(BaseModel):
    total_usd: Decimal
    pages_count: int
    tokens_input: int
    tokens_output: int
    daily_breakdown: list[DailyBreakdown]


class CostEstimateRequest(BaseModel):
    campaign_id: UUID
    keyword_count: int


class CostEstimateOut(BaseModel):
    model: str
    keyword_count: int
    min_usd: Decimal
    max_usd: Decimal
    estimated_tokens: int


class ProjectCostSummary(BaseModel):
    project_id: UUID
    project_name: str
    total_usd: Decimal
    pages_count: int
    tokens_input: int
    tokens_output: int
    budget_usd: Decimal = Decimal("0")
    budget_percent_used: Decimal = Decimal("0")
    budget_alert_level: str = "none"
