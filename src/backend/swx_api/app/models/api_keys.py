# This model was generated using swx CLI.
from typing import Optional, List
from datetime import datetime, timezone
import uuid

from sqlmodel import SQLModel, Field, Relationship

from swx_api.core.models.base import Base


class ApiKeysBase(Base):
    name: str = Field(
        default="Unnamed Key",
        description="Human-readable name for the API key"
    )
    revoked: bool = Field(
        default=False,
        description="Whether the key has been revoked"
    )
    usage_count: int = Field(
        default=0,
        description="Number of times the key has been used"
    )
    expires_at: datetime = Field(
        nullable=False,
        description="Expiration timestamp"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp (defaults to now)"
    )



class ApiKeys(ApiKeysBase, table=True):
    __tablename__ = "api_keys"
    __table_args__ = {"extend_existing": True}

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        description="Primary key UUID"
    )
    key: str = Field(
        ...,
        nullable=False,
        description="The actual API key string"
    )
    user_id: uuid.UUID = Field(foreign_key="user.id")




class ApiKeysCreate(SQLModel):
    """
    Model for creating a new API Key.
    Only user_id and optionally expires_at are provided by the client.
    """
    user_id: uuid.UUID

class ApiKeysUpdate(SQLModel):
    key: Optional[str] = None
    name: Optional[str] = None
    revoked: Optional[bool] = None
    usage_count: Optional[int] = None
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    user_id: Optional[uuid.UUID] = None


class ApiKeysRead(SQLModel):
    id: uuid.UUID
    name: str
    revoked: bool
    usage_count: int
    created_at: datetime
    expires_at: datetime
    user_id: uuid.UUID


class ApiKeysReadWithKey(ApiKeysRead):
    key: str


class ApiKeysPublic(ApiKeys):
    pass
