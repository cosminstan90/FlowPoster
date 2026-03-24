"""
Thin async wrapper around the Anthropic Python SDK.

- Global semaphore limits concurrency to 3 in-flight requests.
- Exponential back-off on RateLimitError (5 s → 15 s → 45 s).
- Tracks token usage and returns cost alongside the response text.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from decimal import Decimal

import anthropic

from backend.config import settings

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Pricing per-token (USD)
# ------------------------------------------------------------------
_PRICING: dict[str, tuple[Decimal, Decimal]] = {
    # model_id → (input_price_per_token, output_price_per_token)
    "claude-sonnet-4-20250514": (Decimal("0.000003"), Decimal("0.000015")),
    "claude-haiku-4-5-20251001": (Decimal("0.0000008"), Decimal("0.000004")),
}

_DEFAULT_INPUT = Decimal("0.000003")
_DEFAULT_OUTPUT = Decimal("0.000015")

# ------------------------------------------------------------------
# Concurrency gate – shared across all ClaudeClient instances
# ------------------------------------------------------------------
_semaphore = asyncio.Semaphore(3)

# Retry schedule (seconds)
_RETRY_DELAYS = (5, 15, 45)


@dataclass(frozen=True)
class CallResult:
    text: str
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal


class ClaudeClient:
    """One instance per model name; reuse where possible."""

    def __init__(self, model: str) -> None:
        self.model = model
        self._client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        price_in, price_out = _PRICING.get(model, (_DEFAULT_INPUT, _DEFAULT_OUTPUT))
        self._price_in = price_in
        self._price_out = price_out

    async def call(
        self,
        system: str,
        user: str,
        max_tokens: int = 4096,
    ) -> CallResult:
        last_exc: Exception | None = None

        for attempt, delay in enumerate((*_RETRY_DELAYS, None)):
            try:
                async with _semaphore:
                    response = await self._client.messages.create(
                        model=self.model,
                        max_tokens=max_tokens,
                        system=system,
                        messages=[{"role": "user", "content": user}],
                    )

                input_tok = response.usage.input_tokens
                output_tok = response.usage.output_tokens
                cost = (
                    self._price_in * input_tok + self._price_out * output_tok
                )
                text = response.content[0].text if response.content else ""

                return CallResult(
                    text=text,
                    input_tokens=input_tok,
                    output_tokens=output_tok,
                    cost_usd=cost,
                )

            except anthropic.RateLimitError as exc:
                last_exc = exc
                if delay is None:
                    # exhausted all retries
                    break
                logger.warning(
                    "Rate-limited on attempt %d for model %s – retrying in %ds",
                    attempt + 1,
                    self.model,
                    delay,
                )
                await asyncio.sleep(delay)

            except anthropic.APIError as exc:
                logger.error("Anthropic API error (%s): %s", self.model, exc)
                raise

        raise last_exc  # type: ignore[misc]
