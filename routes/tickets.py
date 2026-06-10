from fastapi import APIRouter, Cookie, HTTPException, status
from ..database import SessionDep
from ..models import Tickets, TicketCreateRequest, Users, Conversations, Messages, Content
from sqlmodel import select, func, and_
from sqlalchemy.orm import aliased
import nanoid
from ..services.conversations import create_ticket_conversation
from .auth import get_uuid,get_current_user
from enum import Enum
from datetime import datetime
import uuid
from pydantic import BaseModel

router = APIRouter(prefix="/tickets")

#Ticket statuses:
# Open (in progress by support team), 
# Awaiting (Awaiting response from user), 
# Solved (ticket issue resolved)

class TicketStatus(str, Enum):
    open = "open",
    pending = "pending",
    closed = "closed",
    resolved = "resolved"

class TicketMessage(BaseModel):
    content: Content | None = None
    sent_at: datetime | str | None = None

class TicketDetailsResponse(BaseModel):
    id: int
    ticket_ref : str
    conversation_id: str
    customer_name: str | None # Resolved via the first join
    agent_name: str | None    # Resolved via the second join
    issue: str
    status: str
    priority: str
    last_message: TicketMessage | None
    created_at: datetime
    updated_at: datetime


@router.get("/")
async def get_tickets(session:SessionDep, page:int = 1, support_session:str = Cookie(None)):
    user_id = await get_uuid(support_session)
    
    try:

        # 2. Construct the high-performance SQLModel query layout
        query = (
            select(
                Tickets,
                Conversations.customer_name,
                Conversations.agent_name,
                Messages.content,
                Messages.sent_at
            )
            # LEFT JOIN for the customer mapping
            .join(Conversations, Tickets.conversation_id == Conversations.id, isouter = True)
            .join(Messages, Conversations.last_message_id == Messages.id, isouter = True)
            # Filter rows by target user_id parameter matching your raw WHERE clause
            .where(Tickets.customer_id == user_id)
            .order_by(Tickets.created_at.desc())
        )

        # 3. Execute the asynchronous database query
        result =  session.exec(query)
        
        # 4. Parse rows into structured objects
        ticket_list = []
        for row in result.all():
            # row is a tuple: (Tickets_object, "Customer Name", "Agent Name")
            ticket_obj = row[0]
            latest_message = TicketMessage(content=row.content, sent_at=row.sent_at)
            last_message = latest_message.model_dump(mode='json') if (latest_message.content and latest_message.sent_at) else None
            # Map the attributes dynamically right out of the join tuple
            ticket_data = TicketDetailsResponse(
                id=ticket_obj.id,
                ticket_ref = ticket_obj.ticket_ref,
                conversation_id = ticket_obj.conversation_id,
                customer_name= row.customer_name,
                agent_name= row.agent_name,
                issue= ticket_obj.issue,
                status= ticket_obj.status,
                priority=ticket_obj.priority,
                created_at=ticket_obj.created_at,
                updated_at= ticket_obj.updated_at,
                last_message= last_message
            )
            ticket_list.append(ticket_data)

        return ticket_list

    except Exception as e:
        print(f"Database extraction failure: {e}")
        raise HTTPException(status_code=500, detail="Internal server transaction error")
 
@router.get("/support")
async def get_agent_tickets(session:SessionDep, page:int = 1, support_session:str = Cookie(None)):
        user = get_current_user(support_session)["user"]
        if(user.role not in ['SUPPORT_AGENT', 'ADMIN']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized request."
            )
        agent_id = await get_uuid(support_session)
        try:
            # 2. Construct the high-performance SQLModel query layout
            query = (
                select(
                    Tickets,
                    Conversations.customer_name,
                    Conversations.agent_name,
                    Messages.content,
                    Messages.sent_at
                )
                # LEFT JOIN for the customer, agent name mapping
                .join(Conversations, Tickets.conversation_id == Conversations.id, isouter=True)
                .join(Messages, Messages.id == Conversations.last_message_id,isouter=True)
                # Filter rows by target user_id parameter matching your raw WHERE clause
                .where(Tickets.agent_id == agent_id)
                .order_by(Tickets.created_at.desc())
            )

            # 3. Execute the asynchronous database query
            result =  session.exec(query)
            
            # 4. Parse rows into structured objects
            ticket_list = []
            for row in result.all():
                # row is a tuple: (Tickets_object, "Customer Name", "Agent Name")
                ticket_obj = row[0]
                latest_message = TicketMessage(content=row.content,sent_at=row.sent_at)
                last_message = latest_message.model_dump(mode='json') if (latest_message.content and latest_message.sent_at) else None
                # Map the attributes dynamically right out of the join tuple
                ticket_data = TicketDetailsResponse(
                    id=ticket_obj.id,
                    ticket_ref = ticket_obj.ticket_ref,
                    conversation_id = ticket_obj.conversation_id,
                    customer_name= row.customer_name,
                    agent_name= row.agent_name,
                    issue= ticket_obj.issue,
                    status= ticket_obj.status,
                    priority=ticket_obj.priority,
                    created_at=ticket_obj.created_at,
                    updated_at= ticket_obj.updated_at,
                    last_message= last_message
                )
                ticket_list.append(ticket_data)

            return ticket_list

        except Exception as e:
            print(f"Database extraction failure: {e}")
            raise HTTPException(status_code=500, detail="Internal server transaction error")


@router.post("/create-ticket")
async def create_ticket(ticketRequest:TicketCreateRequest, last_message_id:int, session:SessionDep, support_session:str = Cookie(None)):

    customer_id = await get_uuid(support_session)

    print("uuid from create-ticket"+customer_id)

    tkt_ref = f"TKT-{nanoid.generate(size=10)}"

    agent_id = await find_support_agent(session=session)
    

    ticket = Tickets(ticket_ref=tkt_ref, status='open', customer_id=customer_id,agent_id=agent_id, issue = ticketRequest.issue, priority = ticketRequest.priority)

    convo = create_ticket_conversation(session=session, last_message_id=last_message_id,ticket=ticket)
    ticket.conversation_id = convo.id
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket

@router.get("/agents")
async def find_support_agent(session:SessionDep):
    """Finds support agent with least no. of pending tickets"""
#     query = text("""
# SELECT agents.id, (SELECT COUNT(id) from tickets where agent_id =agents.id and status IN ('open','pending') )
# as tkt_count
# FROM (
# SELECT id, full_name
# FROM Users 
# WHERE user_role = 'SUPPORT_AGENT'
# ) as agents 
# ORDER BY tkt_count
# LIMIT 1
# """)

    try:
        # Construct a high-performance grouped join query layout
        query = (
            select(
                Users.id,
                # COUNT(Tickets.id) aggregates cleanly per agent group
                func.count(Tickets.id).label("tkt_count")
            )
            # 1. Start with support agents only (Collapses the nested inner subquery)
            .where(Users.user_role == "SUPPORT_AGENT")
            
            # 2. LEFT JOIN with tickets matching your target condition flags
            .join(
                Tickets,
                and_(
                    Tickets.agent_id == Users.id,
                    Tickets.status.in_(["open", "pending"])
                ),
                isouter=True # Essential to include agents who currently have 0 tickets!
            )
            
            # 3. Group by the Agent ID to run the math cleanly
            .group_by(Users.id)
            
            # 4. Order by your calculated count ascending (least busy first)
            .order_by(func.count(Tickets.id).asc())
            
            # 5. Grab just the top single matching record (LIMIT 1)
            .limit(1)
        )

        # Execute the asynchronous query pass
        result = session.exec(query)
        
        # Extract the first matching row tuple: (agent_id, tkt_count)
        first_row = result.first()
        
        if not first_row:
            # Reverts to None cleanly if you haven't seeded any support agents yet
            return None
            
        # Return just the raw string ID of the chosen agent
        chosen_agent_id = first_row[0]
        print(f"Assigning incoming ticket payload to Agent ID: {chosen_agent_id}")
        return chosen_agent_id

    except Exception as e:
        print(f"Agent routing calculation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate agent availability matrix")
