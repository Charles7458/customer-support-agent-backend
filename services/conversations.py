from ..models import Users, Conversations,Tickets
from ..database import SessionDep
from sqlmodel import select
import uuid

def create_conversation(session:SessionDep, conversation_id:str,user_id:str|uuid.UUID, ticket:Tickets | None):
    customer_name = session.exec(select(Users.full_name).select_from(Users).where(Users.id==user_id)).one()
    conversation = Conversations(id=conversation_id, title="Support Chat with Nexus AI", status='ACTIVE',customer_id=user_id,customer_name=customer_name)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    print("Conversation created"+user_id)
    return conversation

def create_ticket_conversation(session:SessionDep, ticket:Tickets):
    customer_name = session.exec(select(Users.full_name).select_from(Users).where(Users.id==ticket.customer_id)).one()
    agent_name = session.exec(select(Users.full_name).select_from(Users).where(Users.id==ticket.agent_id)).one()
    conversation = Conversations(id=ticket.ticket_ref[4:],
                                title=ticket.ticket_ref+" - "+ticket.issue, 
                                status="open", 
                                customer_id=ticket.customer_id, 
                                customer_name = customer_name, 
                                agent_id=ticket.agent_id, 
                                agent_name=agent_name
                                )
    
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    print("Conversation created"+ticket.ticket_ref)
    return conversation
