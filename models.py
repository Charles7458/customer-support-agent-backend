from sqlmodel import Field, SQLModel
import datetime
import uuid
from typing import Literal
from enum import Enum

class UserRole(str, Enum):
    CUSTOMER = "CUSTOMER"
    SUPPORT_STAFF = "SUPPORT_STAFF"
    ADMIN = "ADMIN"

class Faqs(SQLModel, table=True):
    faq_id: int | None = Field(default=None,primary_key=True)
    question: str
    answer: str
    keywords: str

class Users(SQLModel, table=True):
    user_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    full_name: str
    email: str
    password_hash: str
    user_role: UserRole = Field(default=UserRole.CUSTOMER)
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now
    )
    updated_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now
    )
    is_deleted: bool = Field(default=False)


class Tickets(SQLModel, table=True):
    ticket_id: int | None = Field(default=None,primary_key=True)
    ticket_ref:str | None = Field(default=None)
    user_id: uuid.UUID = Field(foreign_key="users.user_id")
    issue: str
    priority: str | None = Field(default="low")
    status: str | None = Field(default="open")
    support_agent: uuid.UUID | None = Field(default=None)
    created_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now
    )
    updated_at: datetime.datetime = Field(
        default_factory=datetime.datetime.now
    )

# class Conversations(SQLModel, table=True):
#     conv_id: str | None = Field(default=None)
#     created_at: datetime.datetime = Field(
#         default_factory=datetime.datetime.now
#     )
#     updated_at: datetime.datetime = Field(
#         default_factory=datetime.datetime.now
#     )

# class Chats(SQLModel, table=True):
#     chat_id: int
#     conv_id: str = Field(foreign_key="conversations.conv_id")
#     role: Literal['CUSTOMER', 'AI', 'SUPPORT_STAFF']
#     message: str