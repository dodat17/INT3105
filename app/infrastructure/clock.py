from datetime import UTC, datetime
from typing import cast

from sqlalchemy import text
from sqlalchemy.orm import Session


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class DatabaseClock:
    def __init__(self, session: Session) -> None:
        self._session = session

    def now(self) -> datetime:
        if self._session.bind is not None and self._session.bind.dialect.name == "postgresql":
            return cast(datetime, self._session.scalar(text("SELECT clock_timestamp()")))
        return datetime.now(UTC)
