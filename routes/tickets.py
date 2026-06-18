from fastapi import APIRouter, Cookie, HTTPException, status
from database import SessionDep
from models import Tickets, TicketCreateRequest, SupportTicketCreateRequest, TicketPriority
from models import Users, Conversations, Messages, Content, TicketStatus
from sqlmodel import select, func, and_, col
import nanoid
from services.conversations import create_ticket_conversation
from auth import get_uuid,get_current_user
from datetime import datetime
from pydantic import BaseModel
from config import logger

router = APIRouter(prefix="/tickets")

#Ticket statuses:
# open (in progress by support team), 
# pending,
# closed,
# resolved (ticket issue resolved)



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
    created_by: str
    creator_role: str
    updated_at: datetime

class TicketUpdateRequest(BaseModel):
    ticket_id: int
    issue: str
    status: TicketStatus
    priority: TicketPriority

class ResponseGenRequest(BaseModel):
    prompt:str
    message:str

@router.get("/")
async def get_tickets(session:SessionDep, search:str | None = None, tkt_status:TicketStatus | None = None, priority: TicketPriority | None = None, page:int = 1, per_page:int = 10, support_session:str = Cookie(None)):
    customer_id = await get_uuid(support_session)
    
    try:
        # 1. Count total and pending tickets
        count_query = (
            select(
                func.count(Tickets.id).label("total"),
                func.count(Tickets.id).filter(Tickets.status==TicketStatus.open or Tickets.status==TicketStatus.pending).label("pending")
            )
            .where(Tickets.customer_id == customer_id)
        )

        counts_result = await session.exec(count_query)
        counts = counts_result.one()

        total_count = counts.total
        pending_count = counts.pending

        print("total:",total_count," pending:",pending_count)

        # 2. Construct the high-performance SQLModel query layout
        query = (
            
        )

        conditions = []
        if(search):
            conditions.append(col(Tickets.issue).contains(search))
        if(tkt_status):
            conditions.append(Tickets.status == tkt_status)
        if(priority):
            conditions.append(Tickets.priority == priority)

        query = (select(
                Tickets,
                Conversations.customer_name,
                Conversations.agent_name,
                Messages.content,
                Messages.sent_at,
                Users.full_name.label("creator_name"),
                Users.user_role.label("creator_role")
            )
            .join(Conversations, Tickets.conversation_id == Conversations.id, isouter = True)
            .join(Messages, Conversations.last_message_id == Messages.id, isouter = True)
            .join(Users, Tickets.created_by == Users.id,isouter=True)
            .where(and_(Tickets.customer_id == customer_id,*conditions))
            .order_by(Tickets.updated_at.desc()).offset(per_page*(page-1)).limit(per_page)
        )
        

        # if(search is None and tkt_status is None):
        #     query.where(Tickets.customer_id == customer_id)
        # elif(search and tkt_status):
        #     query.where(Tickets.customer_id == customer_id and col(Tickets.issue).contains(search) and Tickets.status == tkt_status)
        # elif(search):
        #     query.where(Tickets.customer_id == customer_id and col(Tickets.issue).contains(search))
        # else:
        #     query.where(Tickets.customer_id == customer_id and Tickets.status == tkt_status)


        # 3. Execute the asynchronous database query
        result = await session.exec(query)
        
        # 4. current count
        current_count_query = select(func.count(Tickets.id)).where(and_(Tickets.customer_id == customer_id, *conditions))

        current_count_res = await session.exec(current_count_query)
        current_count = current_count_res.one()


        # 5. Parse rows into structured objects
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
                created_by=  row.creator_name if(row.creator_name is not None) else ticket_obj.creator_type,
                creator_role= row.creator_role if(row.creator_role is not None) else ticket_obj.creator_type,
                updated_at= ticket_obj.updated_at,
                last_message= last_message
            )
            ticket_list.append(ticket_data)

        return {
                "total": total_count,
                "current": current_count,
                "pending": pending_count,
                "ticket_list": ticket_list
            }

    except Exception:
        logger.error("Get Tickets Failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server transaction error")
 
@router.get("/support/")
async def get_agent_tickets(session:SessionDep, search:str | None = None, tkt_status:TicketStatus | None = None, priority:TicketPriority | None = None, page:int = 1, per_page:int=10,support_session:str = Cookie(None)):
        user = get_current_user(support_session)["user"]
        if(user.role not in ['SUPPORT_AGENT', 'ADMIN']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized request."
            )
        agent_id = await get_uuid(support_session)
        try:
            # 1. Count total and pending tickets
            count_query = (
                select(
                    func.count(Tickets.id).label("total"),
                    func.count(Tickets.id).filter(Tickets.status==TicketStatus.open or Tickets.status==TicketStatus.pending).label("pending")
                )
                .where(Tickets.agent_id == agent_id)
            )

            counts_result = await session.exec(count_query)
            counts = counts_result.one()

            total_count = counts.total
            pending_count = counts.pending

            # 2. Construct the high-performance SQLModel query layout
            

            conditions = []

            if(search):
                conditions.append(col(Tickets.issue).contains(search))
            if(tkt_status):
                conditions.append(Tickets.status == tkt_status)
            if(priority):
                conditions.append(Tickets.priority == priority)

            query = (
                select(
                    Tickets,
                    Conversations.customer_name,
                    Conversations.agent_name,
                    Messages.content,
                    Messages.sent_at,
                    Users.full_name.label("creator_name"),
                    Users.user_role.label("creator_role")
                )
                # LEFT JOIN for the customer, agent name mapping
                .join(Conversations, Tickets.conversation_id == Conversations.id, isouter=True)
                .join(Messages, Messages.id == Conversations.last_message_id,isouter=True)
                .join(Users, Tickets.created_by == Users.id,isouter=True)
                .where(and_(Tickets.agent_id == agent_id,*conditions))
                # Filter rows by target user_id parameter matching your raw WHERE clause
                .order_by(Tickets.updated_at.desc()).offset(per_page*(page-1)).limit(per_page)
            )

            # if(search is None and tkt_status is None and priority is None):
            #     query.where(Tickets.agent_id == agent_id)
            # elif(search and tkt_status and priority):
            #     query.where(Tickets.agent_id == agent_id and col(Tickets.issue).contains(search) and Tickets.status == tkt_status and Tickets.priority == priority)
            # elif(search and priority and tkt_status is None):
            #     query.where(Tickets.agent_id == agent_id and col(Tickets.issue).contains(search) and Tickets.priority == priority)
            # elif(search and tkt_status):
            #     query.where(Tickets.agent_id == agent_id and col(Tickets.issue).contains(search) and Tickets.status == tkt_status)
            # elif(search):
            #     query.where(Tickets.agent_id == agent_id and col(Tickets.issue).contains(search))
            # else:
            #     query.where(Tickets.agent_id == agent_id and Tickets.status == tkt_status)


            # 3. Execute the asynchronous database query
            result = await session.exec(query)

            # 4. current count
            current_count_query = select(func.count(Tickets.id))
    
            current_count_query.where(and_(Tickets.agent_id == agent_id, *conditions))
    
            current_count_res = await session.exec(current_count_query)
            current_count = current_count_res.one()
            
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
                    created_by=  row.creator_name if(row.creator_name is not None) else ticket_obj.creator_type,
                    creator_role= row.creator_role if(row.creator_role is not None) else ticket_obj.creator_type,
                    updated_at= ticket_obj.updated_at,
                    last_message= last_message
                )
                ticket_list.append(ticket_data)

            return {
                "total": total_count,
                "current": current_count,
                "pending": pending_count,
                "ticket_list": ticket_list
            }

        except Exception as e:
            print(f"Database extraction failure: {e}")
            logger.error("Get Tickets for agent failed", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server transaction error")

# Ticket creation for customers
@router.post("/create-ticket")
async def create_ticket(ticketRequest:TicketCreateRequest, session:SessionDep, last_message_id: int | None = None, support_session:str = Cookie(None)):

    customer_id = await get_uuid(support_session)
    

    print("uuid from create-ticket",customer_id)

    tkt_ref = f"TKT-{nanoid.generate(size=10)}"

    agent_id = await find_support_agent(session=session)
    

    ticket = Tickets(
        ticket_ref=tkt_ref, 
        status='open', 
        customer_id=customer_id, 
        agent_id=agent_id, 
        issue = ticketRequest.issue, 
        priority = ticketRequest.priority,
        created_by=customer_id,
        creator_type="Human"
    )

    convo = await create_ticket_conversation(session=session, last_message_id=last_message_id,ticket=ticket)
    ticket.conversation_id = convo.id
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)
    return ticket

# Ticket Creation for Support agents and admin
@router.post("/support/create-ticket")
async def create_ticket_support(ticketRequest:SupportTicketCreateRequest, session:SessionDep, last_message_id: int | None = None, support_session:str = Cookie(None)):

    id = await get_uuid(support_session)

    user = get_current_user(support_session)["user"]
    if(user.role not in ['SUPPORT_AGENT', 'ADMIN']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized request."
        )
    
    customer_id = await session.exec(select(Users.id).select_from(Users).where(Users.email==ticketRequest.customer_email)).one()
    

    print("uuid from create-ticket"+id)

    tkt_ref = f"TKT-{nanoid.generate(size=10)}"

    agent_id = ""
    if(ticketRequest.set_me_as_agent):
        agent_id = id
    else:
        agent_id = await find_support_agent(session=session)
    

    ticket = Tickets(
        ticket_ref=tkt_ref, 
        status='open', 
        customer_id=customer_id, 
        agent_id=agent_id, 
        issue = ticketRequest.issue, 
        priority = ticketRequest.priority,
        created_by=id,
        creator_type="Human"
    )

    convo = await create_ticket_conversation(session=session, last_message_id=last_message_id,ticket=ticket)
    ticket.conversation_id = convo.id
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)
    return ticket


@router.put("/update")
async def update_ticket(update: TicketUpdateRequest, session:SessionDep, support_session:str = Cookie(None)):
    print(update)
    role = get_current_user(support_session)["user"].role
    print(role)
    if not role or (role != 'SUPPORT_AGENT' and role != "ADMIN"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)
    
    ticket = await session.get(Tickets, update.ticket_id)
    ticket.issue = update.issue
    ticket.priority = update.priority
    ticket.status = update.status
    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)
    return ticket


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
        result = await session.exec(query)
        
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
        logger.error("Finding support agent failed", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to calculate agent availability matrix")


@router.post("/generate-response")
async def generate_ai_response(input:ResponseGenRequest, support_session:str = Cookie(None)):
    from ..services.orchestrate import generate_message_response

    role = get_current_user(support_session)
    response = await generate_message_response(prompt=input.prompt, message=input.message, role=role)
    return {
        "response": response
    }