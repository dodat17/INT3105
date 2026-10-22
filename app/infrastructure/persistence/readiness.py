from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

ALEMBIC_INI = Path(__file__).resolve().parents[3] / "alembic.ini"


class DatabaseReadiness:
    """NFR-04: ready only when the DB answers and its schema is at the latest migration."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        # Heads come from the migration files shipped with this build; read them once.
        self._heads = set(ScriptDirectory.from_config(Config(str(ALEMBIC_INI))).get_heads())

    def __call__(self) -> dict[str, bool]:
        try:
            with self._session_factory() as session:
                context = MigrationContext.configure(session.connection())
                current = set(context.get_current_heads())
        except SQLAlchemyError:
            return {"database": False, "migrations": False}
        return {"database": True, "migrations": current == self._heads}
