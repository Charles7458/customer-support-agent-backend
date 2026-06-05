from typing import Literal
from ..database import SessionDep
from sqlmodel import select
from ..models import TicketCreateRequest, Faqs
from ..routes.tickets import create_ticket
from fastapi import Cookie

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

async def create_a_ticket(issue:str,priority:Priority, session:SessionDep, support_session:str = Cookie(None)):
    ticket = TicketCreateRequest(issue=issue,priority= priority)
    try:
        ticket = await create_ticket(ticket, session, support_session)
        return ticket.model_dump(mode='json')
    except Exception as e:
        print("Gemini agent couldn't create ticket!!!")
        print(e)
        return "Couldn't create ticket"
