from models import Users, Conversations,Tickets
from database import SessionDep
from sqlmodel import select
import uuid

async def create_conversation(session:SessionDep, conversation_id:str,user_id:str|uuid.UUID):
    result = await session.exec(select(Users.full_name).select_from(Users).where(Users.id==user_id))
    customer_name = result.one()
    conversation = Conversations(id=conversation_id, title="Support Chat with Nexus AI", status='ACTIVE',customer_id=user_id,customer_name=customer_name)
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    print("Conversation created"+user_id)
    return conversation

async def create_ticket_conversation(session:SessionDep, last_message_id:int, ticket:Tickets):
    result = await session.exec(select(Users.full_name).select_from(Users).where(Users.id==ticket.customer_id))
    customer_name = result.one()
    result2 = await session.exec(select(Users.full_name).select_from(Users).where(Users.id==ticket.agent_id))
    agent_name = result2.one()
    conversation = Conversations(id='conv-'+ticket.ticket_ref[4:],
                                title=ticket.ticket_ref+" - "+ticket.issue, 
                                status="open", 
                                customer_id=ticket.customer_id, 
                                customer_name = customer_name, 
                                agent_id=ticket.agent_id, 
                                agent_name=agent_name,
                                last_message_id = last_message_id
                                )
    
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    print("Conversation created"+ticket.ticket_ref)
    return conversation
