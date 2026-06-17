from sqlmodel import Field, SQLModel
import sqlalchemy as sa
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
# from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone
import uuid
from enum import Enum
from pydantic import BaseModel
import nanoid


class UserRole(str, Enum):
    CUSTOMER = "CUSTOMER"
    AI = "AI"
    SUPPORT_AGENT = "SUPPORT_AGENT"
    ADMIN = "ADMIN"

class UserType(str, Enum):
    Human = "Human"
    Nexus_AI = "Nexus AI"

class TicketPriority(str, Enum):
    low = 'low'
    medium = 'medium'
    high = 'high'

class TicketStatus(str, Enum):
    open = "open",
    pending = "pending",
    closed = "closed",
    resolved = "resolved"

class ChatStatus(str, Enum):
    CLOSED = "CLOSED"
    RESOLVED = "RESOLVED"
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"

class OrderStatus(str, Enum):
    Ordered = "Ordered"
    Shipped = "Shipped"
    Out_For_Delivery = "Out For Delivery"
    Delivered = "Delivered"
    Delivery_Failed = "Delivery Failed"



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
        default_factory=lambda: datetime.now(timezone.utc), sa_type=sa.DateTime(timezone=True)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), sa_type=sa.DateTime(timezone=True)
    )
    is_deleted: bool = Field(default=False)


class Tickets(SQLModel, table=True):
    id: int | None = Field(default=None,primary_key=True)
    ticket_ref:str | None = Field(default=None)
    conversation_id: str | None = Field(default=None,foreign_key="conversations.id")
    customer_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    agent_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    issue: str
    priority: TicketPriority | None = Field(default="low")
    status: TicketStatus | None = Field(default="open")
    created_by: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    creator_type: UserType
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), sa_type=sa.DateTime(timezone=True)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), sa_type=sa.DateTime(timezone=True)
    )


class Conversations(SQLModel, table=True):
    id: str | None = Field(default=None,primary_key=True)
    title: str
    status: str
    customer_id: uuid.UUID = Field(foreign_key="users.id")
    customer_name: str
    agent_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    agent_name: str | None = Field(default=None)
    last_message_id: int | None = Field(default=None, foreign_key="messages.id")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), sa_type=sa.DateTime(timezone=True)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), sa_type=sa.DateTime(timezone=True)
    )


class Messages(SQLModel, table=True):
    id: int | None = Field(primary_key=True)
    conversation_id: str = Field(foreign_key="conversations.id")
    role: UserRole
    content: dict = Field(sa_column=Column(JSONB))
    sent_at: datetime = Field(default_factory= lambda: datetime.now(timezone.utc), sa_type=sa.DateTime(timezone=True))

class Orders(SQLModel, table=True):
    id: str | None = Field(default_factory = lambda: f"#{nanoid.generate(size=11)}", primary_key=True)
    customer_id : uuid.UUID = Field(foreign_key="users.id")
    product_name: str
    amount: int
    status : OrderStatus
    tracking_id : str | None = Field(unique=True)
    order_date: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc), sa_type=sa.DateTime(timezone=True))
    last_update: datetime | None = Field(default_factory = lambda: datetime.now(timezone.utc), sa_type=sa.DateTime(timezone=True))

class Tracking(SQLModel, table=True):
    id: int | None = Field(primary_key=True)
    order_id: str = Field(foreign_key="orders.id")
    updates: str | None = Field(default=None)
    carrier: str | None = Field(default=None)
    status: OrderStatus
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc), sa_type=sa.DateTime(timezone=True))
    

class UserRole(str, Enum):
    CUSTOMER = "CUSTOMER",
    AI = "AI"
    SUPPORT_AGENT = "SUPPORT_AGENT"
    ADMIN = "ADMIN"

class OrderCard(BaseModel):
    order_id: str
    product_name: str
    status: str

class Track (BaseModel):
    tracking_id:str
    carrier: str

class Content(BaseModel):
    text:str
    tracking: Tracking | None = None
    order_cards: list[OrderCard] | None = None
    bullet_list: list[str] | None = None

class ChatMessages(BaseModel):
    id: int | None = None
    role: UserRole
    content: Content
    sent_at : datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc), sa_type=sa.DateTime(timezone=True))


class ChatHistoryResponse(BaseModel):
    conversation: Conversations # Your Pydantic schema for the conversation
    messages: list[ChatMessages]

class TicketCreateRequest(BaseModel):
    issue:str
    priority: TicketPriority

class SupportTicketCreateRequest(TicketCreateRequest):
    customer_email: str
    set_me_as_agent:bool

class AgentOrderResponse(BaseModel):
    order_id: str
    product_name:str
    status: OrderStatus

class TrackingResponse(BaseModel):
    updates: str
    timestamp: datetime