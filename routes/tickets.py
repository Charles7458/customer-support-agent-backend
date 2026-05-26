from fastapi import APIRouter
from database import SessionDep
from models import Tickets
import nanoid

router = APIRouter()


@router.get("/tickets")
async def get_tickets(email:str, session:SessionDep):
    pass

@router.post("/create-ticket")
async def create_ticket(ticket:Tickets, session:SessionDep):
    tkt_ref = f"TKT-{nanoid.generate(size=10)}"
    # while(tkt_id)
    #     tkt_id = f"TKT-{nanoid.generate(size=8)}"
    ticket.ticket_ref = tkt_ref
    session.add(ticket)
    session.commit()
