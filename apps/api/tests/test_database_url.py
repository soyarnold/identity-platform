from identity_api.config import normalize_database_url


def test_normalize_database_url_postgres_scheme() -> None:
    assert (
        normalize_database_url("postgres://u:p@host:5432/db")
        == "postgresql+asyncpg://u:p@host:5432/db"
    )


def test_normalize_database_url_postgresql_scheme() -> None:
    assert (
        normalize_database_url("postgresql://u:p@host:5432/db")
        == "postgresql+asyncpg://u:p@host:5432/db"
    )


def test_normalize_database_url_already_asyncpg() -> None:
    url = "postgresql+asyncpg://u:p@host:5432/db"
    assert normalize_database_url(url) == url
