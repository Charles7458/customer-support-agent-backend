from fastapi import APIRouter
from ..database import SessionDep
from ..models import Tickets
from sqlmodel import select
import nanoid

router = APIRouter()

#Ticket statuses:
# Open (in progress by support team), 
# Awaiting (Awaiting response from user), 
# Solved (ticket issue resolved)

@router.get("/tickets")
async def get_tickets(uuid:str, session:SessionDep):
    tickets = session.exec(select(Tickets.ticket_ref, Tickets.issue, Tickets.priority, Tickets.status, Tickets.created_at, Tickets.last_updated).where(Tickets.user_id == uuid))
    return tickets

@router.post("/create-ticket")
async def create_ticket(ticket:Tickets, session:SessionDep):
    tkt_ref = f"TKT-{nanoid.generate(size=10)}"
    # while(tkt_id)
    #     tkt_id = f"TKT-{nanoid.generate(size=8)}"

    ticket.ticket_ref = tkt_ref
    session.add(ticket)
    session.commit()

def find_support_staff() -> str:
    """Finds support agent with least no. of pending tickets"""
    pass