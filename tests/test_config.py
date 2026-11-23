from src.lib.config import normalize_database_url


def test_railway_postgres_url_uses_psycopg() -> None:
    assert (
        normalize_database_url("postgres://spaceship:secret@db.internal:5432/spaceship")
        == "postgresql+psycopg://spaceship:secret@db.internal:5432/spaceship"
    )


def test_railway_postgresql_url_uses_psycopg() -> None:
    assert (
        normalize_database_url("postgresql://spaceship:secret@db.internal:5432/spaceship")
        == "postgresql+psycopg://spaceship:secret@db.internal:5432/spaceship"
    )


def test_local_psycopg_url_stays_unchanged() -> None:
    url = "postgresql+psycopg://spaceship:spaceship@localhost:54329/spaceship"
    assert normalize_database_url(url) == url
