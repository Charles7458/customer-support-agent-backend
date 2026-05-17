from fastapi import FastAPI, Depends
from typing import Annotated
from sqlmodel import Field, Session, SQLModel, create_engine, select
import os
import nanoid
from dotenv import load_dotenv
import datetime
from .models import Faqs, Tickets
from .routes.auth import router as auth_router

load_dotenv()

app = FastAPI()

app.include_router(auth_router)

db_url = os.getenv("database_url")

engine = create_engine(db_url, echo=True)


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


@app.post("/ticket")
async def add_ticket(ticket:Tickets, session: SessionDep) -> None:
    with Session(engine) as session:
        tkt_ref = f"TKT-{nanoid.generate(size=8)}"
        # while(tkt_id)
        #     tkt_id = f"TKT-{nanoid.generate(size=8)}"
        ticket.ticket_ref = tkt_ref

        session.add(ticket)
        session.commit()


    