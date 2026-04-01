"""
Async OpenAI client with the same CallResult interface as ClaudeClient.
"""
from __future__ import annotations

import asyncio
import logging
from decimal import Decimal

from openai import AsyncOpenAI, RateLimitError, APIError

from backend.config import settings
from backend.services.ai.claude_client import CallResult

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Pricing per-token (USD)  —  as of 2026-04
# ------------------------------------------------------------------
_PRICING: dict[str, tuple[Decimal, Decimal]] = {
    "gpt-4o":           (Decimal("0.0000025"),  Decimal("0.00001")),
    "gpt-4o-mini":      (Decimal("0.00000015"), Decimal("0.0000006")),
    "o3-mini":          (Decimal("0.0000011"),  Decimal("0.0000044")),
}
_DEFAULT_INPUT  = Decimal("0.0000025")
_DEFAULT_OUTPUT = Decimal("0.00001")

_semaphore    = asyncio.Semaphore(3)
_RETRY_DELAYS = (5, 15, 45)


class OpenAIClient:
    """One instance per model name; matches ClaudeClient.call() signature."""

    def __init__(self, model: str) -> None:
        self.model = model
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        price_in, price_out = _PRICING.get(model, (_DEFAULT_INPUT, _DEFAULT_OUTPUT))
        self._price_in  = price_in
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
                    response = await self._client.chat.completions.create(
                        model=self.model,
                        max_tokens=max_tokens,
                        messages=[
                            {"role": "system", "content": system},
                            {"role": "user",   "content": user},
                        ],
                    )

                input_tok  = response.usage.prompt_tokens
                output_tok = response.usage.completion_tokens
                cost = self._price_in * input_tok + self._price_out * output_tok
                text = response.choices[0].message.content or ""

                return CallResult(
                    text=text,
                    input_tokens=input_tok,
                    output_tokens=output_tok,
                    cost_usd=cost,
                )

            except RateLimitError as exc:
                last_exc = exc
                if delay is None:
                    break
                logger.warning(
                    "OpenAI rate-limited on attempt %d for %s – retrying in %ds",
                    attempt + 1, self.model, delay,
                )
                await asyncio.sleep(delay)

            except APIError as exc:
                logger.error("OpenAI API error (%s): %s", self.model, exc)
                raise

        raise last_exc  # type: ignore[misc]
