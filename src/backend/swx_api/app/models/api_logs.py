# Cleaned and fixed ApiLogs model

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON
from swx_api.core.models.base import Base


class ApiLogsBase(Base):
    client_name: Optional[str] = Field(default=None, description="Source client (e.g., gpt, cursor, claude)")
    client_version: Optional[str] = Field(default=None, description="Client version string, if provided")

    path: str = Field(..., description="Request path, e.g., /plan-trip")
    status_code: int = Field(..., description="HTTP response status code")
    tool_name: Optional[str] = Field(default=None, description="Name of the tool invoked, e.g., 'plan_trip'")

    request_body: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Request payload (truncated if large)"
    )
    response_body: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Response data returned"
    )

    ip_address: Optional[str] = Field(default=None, description="Client IP address")
    user_agent: Optional[str] = Field(default=None, description="User-Agent header of the request")

    request_time: datetime = Field(..., description="Timestamp of request receipt")
    response_time: datetime = Field(..., description="Timestamp of response completion")
    latency_ms: int = Field(..., description="Response latency in milliseconds")
    auth_status: str = Field(default="unknown", description="Authentication outcome: success, missing, or invalid")

class ApiLogs(ApiLogsBase, table=True):
    __tablename__ = "api_logs"
    __table_args__ = {"extend_existing": True}

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        description="Primary key UUID"
    )

    api_key_id: Optional[uuid.UUID] = Field(
        foreign_key="api_keys.id",
        description="Foreign key to API key used"
    )

    user_id: Optional[uuid.UUID] = Field(
        foreign_key="user.id",
        description="User who made the request"
    )


class ApiLogsCreate(SQLModel):
    api_key_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    client_name: Optional[str] = None
    client_version: Optional[str] = None
    path: str
    status_code: int
    tool_name: Optional[str] = None

    request_body: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    response_body: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_time: datetime
    response_time: datetime
    latency_ms: int
    auth_status: str


class ApiLogsUpdate(SQLModel):
    api_key_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    client_name: Optional[str] = None
    client_version: Optional[str] = None
    path: Optional[str] = None
    status_code: Optional[int] = None
    tool_name: Optional[str] = None

    request_body: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    response_body: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_time: Optional[datetime] = None
    response_time: Optional[datetime] = None
    latency_ms: Optional[int] = None


class ApiLogsPublic(ApiLogsBase, SQLModel):
    id: uuid.UUID
    api_key_id: Optional[uuid.UUID]
    user_id: Optional[uuid.UUID]
    auth_status: Optional[str]
