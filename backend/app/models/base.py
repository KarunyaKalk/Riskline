import uuid
from sqlalchemy import Column, UUID, ForeignKey
from sqlalchemy.orm import declared_attr
from app.core.database import Base


class OrgScopedMixin:
    """
    Mixin for all tenant-scoped tables to enforce organization isolation from day one.
    Guarantees every table has an `org_id` Foreign Key referencing `organizations.id`.
    """

    @declared_attr
    def org_id(cls):
        return Column(
            UUID(as_uuid=True),
            ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
