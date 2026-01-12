"""Common Pydantic Schemas."""

from uuid import UUID

from pydantic import BaseModel


class UUIDMixin(BaseModel):
    """Mixin to add a UUID primary key."""

    id: UUID
