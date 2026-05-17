from sqlmodel import Field, SQLModel
import datetime

class Faqs(SQLModel, table=True):
    faq_id: int | None = Field(default=None,primary_key=True)
    question: str
    answer: str
    keywords: str

class Users(SQLModel, table=True):
    user_id: int | None = Field(default=None, primary_key=True)
    full_name: str
    email: str
    password_hash: str
    user_role: str = Field(default='USER')
    created_at: datetime.datetime | None = Field(default=None)


class Tickets(SQLModel, table=True):
    ticket_id: int | None = Field(default=None,primary_key=True)
    ticket_ref:str | None = Field(default=None)
    user_id: int = Field(foreign_key="users.userId")
    issue: str
    priority: str | None = Field(default="low")
    status: str | None = Field(default="new")
    created_at: datetime.datetime | None = Field(default=None)