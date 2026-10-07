from datetime import UTC, datetime
from typing import cast

from sqlalchemy import func, select
from sqlalchemy.orm import Session


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class DatabaseClock:
    """Read the decision time from the same database session as the use case."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def now(self) -> datetime:
        function = (
            func.clock_timestamp() if self._dialect == "postgresql" else func.current_timestamp()
        )
        value = cast(datetime, self._session.scalar(select(function)))
        return value if value.tzinfo else value.replace(tzinfo=UTC)

    @property
    def _dialect(self) -> str:
        return self._session.get_bind().dialect.name
