from collections.abc import Iterator

from sqlmodel import Session, create_engine

from src.lib.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
