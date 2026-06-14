from sqlmodel import Field, SQLModel
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
# from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid
from enum import Enum
from pydantic import BaseModel

class UserRole(str, Enum):
    CUSTOMER = "CUSTOMER"
    AI = "AI"
    SUPPORT_AGENT = "SUPPORT_AGENT"
    ADMIN = "ADMIN"

class Priority(str, Enum):
    low = 'low',
    medium = 'medium',
    high = 'high'

class ChatStatus(str, Enum):
    CLOSED = "CLOSED",
    RESOLVED = "RESOLVED",
    PENDING = "PENDING",
    ACTIVE = "ACTIVE"


class Faqs(SQLModel, table=True):
    id: int | None = Field(default=None,primary_key=True)
    question: str
    answer: str
    keywords: str

class Users(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    full_name: str
    email: str
    password_hash: str
    user_role: UserRole = Field(default=UserRole.CUSTOMER)
    created_at: datetime = Field(
        default_factory=datetime.now
    )
    updated_at: datetime = Field(
        default_factory=datetime.now
    )
    is_deleted: bool = Field(default=False)


class Tickets(SQLModel, table=True):
    id: int | None = Field(default=None,primary_key=True)
    ticket_ref:str | None = Field(default=None)
    conversation_id: str | None = Field(default=None,foreign_key="conversations.id")
    customer_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    agent_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    issue: str
    priority: str | None = Field(default="low")
    status: str | None = Field(default="open")
    created_by: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    creator_type: str
    created_at: datetime = Field(
        default_factory=datetime.now
    )
    updated_at: datetime = Field(
        default_factory=datetime.now
    )


class Conversations(SQLModel, table=True):
    id: str | None = Field(default=None,primary_key=True)
    title: str
    status: str
    customer_id: uuid.UUID
    customer_name: str
    agent_id: uuid.UUID | None = Field(default=None)
    agent_name: str | None = Field(default=None)
    last_message_id: int | None = Field(default=None, foreign_key="messages.id")
    created_at: datetime = Field(
        default_factory=datetime.now
    )
    updated_at: datetime = Field(
        default_factory=datetime.now
    )


class Messages(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    conversation_id: str = Field(foreign_key="conversations.id")
    role: UserRole
    content: dict = Field(sa_column=Column(JSONB))
    sent_at: datetime = Field(default_factory= datetime.now)

class UserRole(str, Enum):
    CUSTOMER = "CUSTOMER",
    AI = "AI"
    SUPPORT_AGENT = "SUPPORT_AGENT"
    ADMIN = "ADMIN"

class OrderCard(BaseModel):
    order_id: str
    status: str

class Tracking(BaseModel):
    tracking_id:str
    carrier: str

class Content(BaseModel):
    text:str
    tracking: Tracking | None = None
    order_card: OrderCard | None = None
    bullet_list: list[str] | None = None

class ChatMessages(BaseModel):
    id: int | None = None
    role: UserRole
    content: Content
    sent_at : datetime | None = Field(default_factory=datetime.now)


class ChatHistoryResponse(BaseModel):
    conversation: Conversations # Your Pydantic schema for the conversation
    messages: list[ChatMessages]

class TicketCreateRequest(BaseModel):
    issue:str
    priority: Priority

class SupportTicketCreateRequest(TicketCreateRequest):
    customer_email: str
    set_me_as_agent:bool