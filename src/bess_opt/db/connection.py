"""SQLite connection management via SQLAlchemy."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from bess_opt.utils.helpers import resolve_path

_engines: dict = {}
_session_factories: dict = {}


def get_engine(db_path: str = "database/bess_data.db"):
    """Engines are cached per resolved db_path (not globally), so pointing at
    different SQLite files within the same process - e.g. a real DB and a
    test DB - doesn't silently reuse the wrong connection."""
    key = str(resolve_path(db_path))
    if key not in _engines:
        full_path = resolve_path(db_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        _engines[key] = create_engine(f"sqlite:///{full_path}", future=True)
    return _engines[key]


def get_session_factory(db_path: str = "database/bess_data.db"):
    key = str(resolve_path(db_path))
    if key not in _session_factories:
        _session_factories[key] = sessionmaker(bind=get_engine(db_path), future=True)
    return _session_factories[key]


def reset_engine_cache(db_path: str = "database/bess_data.db") -> None:
    """Dispose and drop the cached engine for db_path. Call this before
    deleting/recreating a SQLite file out from under an open engine
    (e.g. between test runs), to avoid stale-connection 'readonly database'
    errors on some platforms."""
    key = str(resolve_path(db_path))
    engine = _engines.pop(key, None)
    if engine is not None:
        engine.dispose()
    _session_factories.pop(key, None)


@contextmanager
def get_session(db_path: str = "database/bess_data.db"):
    session = get_session_factory(db_path)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db_from_schema(db_path: str = "database/bess_data.db",
                         schema_path: str = "database/schema.sql"):
    """Execute schema.sql against the target SQLite DB (idempotent, uses IF NOT EXISTS)."""
    engine = get_engine(db_path)
    schema_sql = Path(resolve_path(schema_path)).read_text()
    with engine.begin() as conn:
        for statement in schema_sql.split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
