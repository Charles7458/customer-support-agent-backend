from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
import os
from dotenv import load_dotenv
from .routes.auth import router as auth_router
from .routes.users import router as user_router
from .routes.chat import router as chat_router
from .routes.tickets import router as ticket_router
from .routes.support_chat import router as support_chat_router
from .routes.orders import router as order_router
from .routes.faq import router as faq_router

load_dotenv()

app = FastAPI()

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(chat_router)
app.include_router(ticket_router)
app.include_router(support_chat_router)
app.include_router(order_router)
app.include_router(faq_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL")],  # your frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_url = os.getenv("ASYNC_DB_URL")

engine = create_async_engine(db_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
