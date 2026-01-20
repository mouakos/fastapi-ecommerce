"""Common mixins for SQLModel models.

These mixins can be used to add common fields like timestamps and UUIDs to your models.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import DateTime, Field, SQLModel, func

from app.utils.datetime import utcnow


class TimestampMixin(SQLModel):
    """Mixin to add created_at and updated_at timestamps."""

    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(  # type: ignore[call-overload]
        default_factory=utcnow,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "nullable": False,
            "server_default": func.now(),
            "onupdate": func.now(),
        },
    )


class ModelBase(SQLModel):
    """Base model with UUID primary key."""

    id: UUID = Field(default_factory=uuid4, primary_key=True)
