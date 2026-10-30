"""Shared kernel ports. Module-specific ports live in each module's ``ports.py``."""

from dataclasses import dataclass
from datetime import datetime
from types import TracebackType
from typing import Protocol, Self


@dataclass(frozen=True)
class Page[T]:
    items: list[T]
    page: int
    page_size: int
    total_items: int


class Clock(Protocol):
    def now(self) -> datetime: ...


class UnitOfWork(Protocol):
    """One transaction per use case; each module extends it with only the ports it may use."""

    @property
    def clock(self) -> Clock: ...

    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...
    def commit(self) -> None: ...
