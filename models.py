from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    api_key: str = Field(index=True, unique=True)
    role: str = Field(default="member")  # admin or member
    credits: int = Field(default=100)

class Rule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    pattern: str
    action: str  # AUTO_ACCEPT, AUTO_REJECT
    description: Optional[str] = None

class Command(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    command_text: str
    status: str  # pending, accepted, rejected, executed
    result: Optional[str] = None
    credits_deducted: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int]
    action: str
    details: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)