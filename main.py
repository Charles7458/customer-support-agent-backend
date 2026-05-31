from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated
from sqlmodel import Field, Session, SQLModel, create_engine, select
import os
import nanoid
from dotenv import load_dotenv
import datetime
from .models import Faqs, Tickets
from .routes.auth import router as auth_router
from .routes.users import router as user_router
from .routes.chat import router as chat_router

load_dotenv()

app = FastAPI()

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(chat_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # your frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_url = os.getenv("database_url")

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

@app.get("/")
async def greet():
    return "Hello World"

@app.get("/faq")
async def fetch_faq_with_keyword(keyword, session: SessionDep) -> list[Faqs]:
    searchStr = '%'+keyword+'%'
    results = session.exec(select(Faqs).where(Faqs.keywords.like(searchStr)))
    faqs = results.all()
    return faqs




    