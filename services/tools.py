from typing import Literal
from ..database import SessionDep
from sqlmodel import select
from ..models import TicketCreateRequest, Tickets, Faqs
from ..routes.tickets import create_ticket
from fastapi import Cookie
from ..routes.auth import get_uuid
from ..services.conversations import create_ticket_conversation
from ..routes.tickets import find_support_agent
import nanoid

Priority = Literal['low' ,'medium' , 'high']

'''
Tools:
    1. Create Ticket(issue, priority)
    2. Get recent Orders(order_id)
    3. Search for FAQs using keywords(keywords)

'''

#Declarations

get_order_declaration = {
    "name": "get_orders",
    "description": "Get recent orders of the corresponding user",
}


create_ticket_declaration = {
    "name": "create_a_ticket",
    "description": "Create a ticket if user's query is only solvable by support team staff",
    "parameters": {
         "type" : "object",
         "properties": {
              "issue" : {
                    "type": "string",
                    "description": "Issue faced by the user"
                },
                "priority" : {
                    "enum" : ["low", "medium", "high"],
                    "description" : "Priority level of the user's issue based on urgency and impact."
                }
         },
    "required": ["issue", "priority"]
    }   
}

get_faq_declaration = {
    "name": "get_faqs",
    "description": "Get relevant FAQs from database using keywords from the users's query",
    "parameters": {
         "type": "object",
         "properties" : {
              "keywords" : {
                    "type": "array",
                    "items": {"type": "string"},
                    "description" : "Keywords present in the user's query used for finding FAQ from database"
                }
         },
    "required" : ["keywords"]
    }
}

# Functions

def get_faqs(keywords:list[str], session:SessionDep) -> list[Faqs]:
    faqs = session.exec(select(Faqs)).all()
    res = []
    for faq in faqs:
            for keyword in keywords:
                if(faq.keywords.find(keyword) != -1):
                    res.append(faq)
                    break
    
    return res


def get_orders(user_id:str):
    pass

async def create_a_ticket(issue:str,priority:Priority, last_message_id:int, session:SessionDep, support_session:str = Cookie(None)):
    try:
        customer_id = await get_uuid(support_session)

        print("uuid from create-ticket"+customer_id)

        tkt_ref = f"TKT-{nanoid.generate(size=10)}"

        agent_id = await find_support_agent(session=session)
        
        ticket = Tickets(
            ticket_ref=tkt_ref, 
            status='open', 
            customer_id=customer_id, 
            agent_id=agent_id, 
            issue = issue, 
            priority =priority,
            creator_type="Nexus AI"
        )

        convo = create_ticket_conversation(session=session, last_message_id=last_message_id,ticket=ticket)
        ticket.conversation_id = convo.id
        session.add(ticket)
        session.commit()
        session.refresh(ticket)
        return ticket.model_dump(mode='json')
    except Exception as e:
        print("Gemini agent couldn't create ticket!!!")
        print(e)
        return "Couldn't create ticket"
