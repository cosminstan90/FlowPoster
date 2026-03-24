"""
Abstract base class for CMS publish adapters.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypedDict

from backend.models.generated_page import GeneratedPage


class PublishResult(TypedDict):
    success: bool
    published_url: str
    remote_id: str


class UnpublishResult(TypedDict):
    success: bool


class ConnectionResult(TypedDict):
    success: bool
    message: str


class PublishAdapter(ABC):
    """Every CMS adapter must implement these three methods."""

    @abstractmethod
    async def publish(self, page: GeneratedPage) -> PublishResult:
        """Push the page to the CMS and return its public URL + remote ID."""
        ...

    @abstractmethod
    async def unpublish(self, page: GeneratedPage) -> UnpublishResult:
        """Revert the page to draft / hidden state in the CMS."""
        ...

    @abstractmethod
    async def test_connection(self) -> ConnectionResult:
        """Verify credentials and connectivity to the CMS."""
        ...
