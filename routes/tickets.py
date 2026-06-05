from fastapi import APIRouter, Cookie, HTTPException, status
from ..database import SessionDep
from ..models import Tickets, TicketCreateRequest
from sqlmodel import select, text
import nanoid
from ..services.conversations import create_ticket_conversation
from .auth import get_uuid,get_current_user
from enum import Enum

router = APIRouter(prefix="/tickets")

#Ticket statuses:
# Open (in progress by support team), 
# Awaiting (Awaiting response from user), 
# Solved (ticket issue resolved)

class TicketStatus(str, Enum):
    open = "open",
    awaiting = "awaiting",
    solved = "solved"

@router.get("/")
async def get_tickets(session:SessionDep, support_sesssion:str = Cookie(None)):
    user_id = await get_uuid(support_sesssion)
    tickets = session.exec(select(Tickets.ticket_ref, Tickets.issue, Tickets.priority, Tickets.status, Tickets.created_at, Tickets.last_updated).where(Tickets.user_id == user_id))
    return tickets.model_dump(mode='json')

@router.get("/support")
async def get_agent_tickets(session:SessionDep, support_session:str = Cookie(None)):
        user = get_current_user(support_session)
        if(user.role != 'SUPPORT_AGENT' and user.role != 'ADMIN'):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized request."
            )
        agent_id = await get_uuid(support_session)
        tickets = session.exec(select(Tickets.ticket_ref, Tickets.issue, Tickets.priority, Tickets.status, Tickets.created_at, Tickets.last_updated).where(Tickets.agent_id == agent_id))
        return tickets.model_dump(mode='json')


@router.post("/create-ticket")
async def create_ticket(ticketRequest:TicketCreateRequest, session:SessionDep, support_session:str = Cookie(None)):

    customer_id = await get_uuid(support_session)

    print("uuid from create-ticket"+customer_id)

    tkt_ref = f"TKT-{nanoid.generate(size=10)}"

    agent_id = find_support_agent(session=session)
    

    ticket = Tickets(ticket_ref=tkt_ref, status='open', customer_id=customer_id,agent_id=agent_id, issue = ticketRequest.issue, priority = ticketRequest.priority)

    convo = create_ticket_conversation(session=session, ticket=ticket)
    ticket.conversation_id = convo.id
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket


def find_support_agent(session:SessionDep):
    """Finds support agent with least no. of pending tickets"""
    query = text("""
SELECT agents.id, (SELECT COUNT(id) from tickets where agent_id =agents.id and status <> 'solved')
as tkt_count
FROM (
SELECT id, full_name
FROM Users 
WHERE user_role = 'SUPPORT_AGENT'
) as agents 
ORDER BY tkt_count
LIMIT 1
""")
    agent = session.exec(query).one()
    print(agent)
    return agent.id