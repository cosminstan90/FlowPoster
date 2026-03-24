from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    message: str

    @classmethod
    def ok(cls, data: T, message: str = "OK") -> "APIResponse[T]":
        return cls(success=True, data=data, message=message)

    @classmethod
    def fail(cls, message: str) -> "APIResponse[None]":
        return cls(success=False, data=None, message=message)
