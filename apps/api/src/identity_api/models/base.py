from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import JSON, TypeDecorator


class JSONType(TypeDecorator):
    """Dialect-aware JSON column: JSONB on Postgres, JSON elsewhere."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):  # type: ignore[no-untyped-def]
        # Prefer JSONB in Postgres for indexing/query performance on metadata.
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import JSONB

            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


class Base(DeclarativeBase):
    """Shared declarative base; all ORM models register on Base.metadata."""

    pass
