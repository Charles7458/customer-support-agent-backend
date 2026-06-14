from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated
from sqlmodel import Session, SQLModel, create_engine, select
import os
from dotenv import load_dotenv
from .models import Faqs
from .routes.auth import router as auth_router
from .routes.users import router as user_router
from .routes.chat import router as chat_router
from .routes.tickets import router as ticket_router
from .routes.support_chat import router as support_chat_router

load_dotenv()

app = FastAPI()

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(chat_router)
app.include_router(ticket_router)
app.include_router(support_chat_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL")],  # your frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_url = os.getenv("DATABASE_URL")

engine = create_engine(db_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
        
SessionDep = Annotated[Session, Depends(get_session)]




#Ticket statuses: 
# New (Created just now), 
# Open (in progress by support team), 
# Awaiting (Awaiting response from user), 
# Solved (ticket issue resolved)


