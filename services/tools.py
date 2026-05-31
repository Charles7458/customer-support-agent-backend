from typing import Literal
from ..database import SessionDep
from sqlmodel import select
from ..models import Tickets, Faqs
from ..routes.tickets import create_ticket

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
                    "type": "string",
                    "description" : "Priority level of the user's issue. Valid values are 'low', 'medium' and 'high'"
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

def create_a_ticket(issue:str,priority:Priority, user_id:str, session:SessionDep):
    ticket = Tickets(issue=issue,priority=priority,status='new', user_id=user_id)
    create_ticket(ticket,session)
