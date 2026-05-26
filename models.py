from sqlmodel import Field, SQLModel
import datetime
import uuid

class Faqs(SQLModel, table=True):
    faq_id: int | None = Field(default=None,primary_key=True)
    question: str
    answer: str
    keywords: str

class Users(SQLModel, table=True):
    user_id: uuid.UUID | None = Field(default_factory=uuid.uuid4, primary_key=True)
    full_name: str
    email: str
    password_hash: str
    user_role: str = Field(default='USER')
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
    status: str | None = Field(default="new")
    created_at: datetime.datetime | None = Field(default=None)
    last_updated: datetime.datetime | None = Field(default=None)

# class ConvMessage(SQLModel, table=True):
#     conv_id: str | None = Field(default=None)
    