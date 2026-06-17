from typing import Literal
from ..database import SessionDep
from sqlmodel import select, and_
from ..models import Tickets, Faqs, Orders, Tracking, AgentOrderResponse, TrackingResponse
from fastapi import Cookie
from ..routes.auth import get_uuid
from ..services.conversations import create_ticket_conversation
from ..routes.tickets import find_support_agent
from datetime import datetime
import nanoid
from ..config import logger

Priority = Literal['low' ,'medium' , 'high']

'''
Tools:
    1. Create Ticket(issue, priority)
    2. Get recent Orders(order_id)
    3. Search for FAQs using keywords(keywords)

'''

#Declarations

get_recent_order_declaration = {
    "name": "get_recent_orders",
    "description": "Gets the order id, product name and status of last 5 orders of the user. Use it if user wants order information but doesn't specify.",
}

get_order_by_month_declaration = {
    "name": "get_order_by_month",
    "description": "Get order id, product name and status of orders placed in a specific month and year which were placed by the corresponding user",
    "parameters": {
        "type": "object",
        "properties": {
            "month": {
                "type": "number",
                "description": "Number corresponding to the month of the order date from 1 to 12. January = 1,..., December = 12"
            },
            "year": {
                "type": "number",
                "description": "Year of the order date. eg. 2004"
            }
        },

        "required": ["month","year"]
    },
}

get_order_by_id_declaration = {
    "name": "get_order_by_id",
    "description": "Get order by a specific order id. Use it if order id of the desired order information is known.",
    "parameters": {
        "type": "object",
        "properties": {
            "order_id": {
                "type": "string",
                "description": "Order ID of the specific order. Order id starts with '#'"
            }
        },
        
        "required": ["order_id"]
    },
}

get_tracking_updates_declaration = {
    "name": "get_tracking_updates",
    "description": "This function gets tracking updates of a specific order including tracking_id and carrier name. Use this only if the user wants to know the updates of an order delivery",
    "parameters": {
        "type": "object",
        "properties": {
            "order_id" : {
                "type": "string",
                "description": "Order ID of the order. Starts with '#' eg. '#C6Thu322W5Q1M''"
            }
        },
        
        "required": ["order_id"]
    },
}


create_ticket_declaration = {
    "name": "create_a_ticket",
    "description": "This function is for creating a ticket. Use this function if the user wants to escalate the issue, create a ticket or wants a refund/replacement or an issue not solvable by chat.",
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
    "description": "Use this function when user asks a FAQ. FAQs such as 'what is the refund policy?'",
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

async def get_faqs(keywords:list[str], session:SessionDep, support_session:str = Cookie(None)) -> list[Faqs]:
    results = await session.exec(select(Faqs))
    res = []
    for faq in results.all():
            for keyword in keywords:
                if(faq.keywords.find(keyword) != -1):
                    res.append(faq)
                    break
    
    return res


async def get_recent_orders(session:SessionDep, support_session:str = Cookie(None)):
    try:
        customer_id = await get_uuid(support_session)
        results = await session.exec(select(Orders.id,Orders.product_name, Orders.status).select_from(Orders).where(Orders.customer_id==customer_id).order_by(Orders.last_update.desc()).limit(5))
        orders = []
        for row in results.all():
            order = AgentOrderResponse(order_id=row.id, product_name = row.product_name, status= row.status)
            orders.append(order)

        return orders
    
    except Exception as e:
        logger.error("agent failed to get recent orders", exc_info=True)
        print(e)
        return "tool call failed"

async def get_orders_by_month(month:int, year:int, session:SessionDep, support_session:str = Cookie(None)):
    # 1. Define the start of the target month
    start_date = datetime(year, month, 1)
    
    # 2. Calculate the start of the NEXT month
    # This handles the year-rollover (e.g., if month is 12, next is Jan of year+1)
    if month == 12:
        next_month_start = datetime(year + 1, 1, 1)
    else:
        next_month_start = datetime(year, month + 1, 1)
    try:
        customer_id = await get_uuid(support_session)
        results = await session.exec(
            select(Orders.id, Orders.product_name, Orders.status)
            .where(
                and_(
                    Orders.customer_id==customer_id,
                    Orders.order_date >= start_date, 
                    Orders.order_date < next_month_start
                )
            )
            .order_by(Orders.last_update.desc())
            )
            
        orders = []

        for row in results.all():
            order = AgentOrderResponse(order_id=row.id, product_name = row.product_name, status= row.status)
            orders.append(order)
        
        return orders
    except Exception:
        logger.error("Get orders by month failed", exc_info=True)
        return "tool call failed"
    
async def get_order_by_id(order_id:str, session:SessionDep, support_session:str = Cookie(None)):
    result = await session.exec(select(Orders.id, Orders.product_name, Orders.status).where(Orders.id==order_id))
    order_result = result.one()
    order = AgentOrderResponse(order_id=order_result.id, product_name=order_result.product_name, status = order_result.status)
    return order
    
async def get_tracking_updates(order_id: str,session:SessionDep, support_session:str = Cookie(None)):
    try:
        order = await session.get(Orders, order_id)
        if order is None:
            return "Order does not exist"
        tracking_id = order.tracking_id
        results = await session.exec(select(Tracking.updates, Tracking.carrier, Tracking.updated_at.label("timestamp")).select_from(Tracking).where(Tracking.order_id==order_id).order_by(Tracking.id))
        updates = []
        carrier = ""
        for row in results.all():
            updates.append(TrackingResponse(updates=row.updates, timestamp=row.timestamp).model_dump(mode='json'))
            carrier = row.carrier

        return {
            "tracking_id": tracking_id,
            "carrier": carrier,
            "updates" : updates
        }
    except Exception:
        logger.error("Agent failed to fetch tracking updates", exc_info=True)
        return "Couldn't fetch order updates"

    

async def create_a_ticket(issue:str,priority:Priority, last_message_id:int, session:SessionDep, support_session:str = Cookie(None)):
    try:
        customer_id = await get_uuid(support_session)

        print("uuid from create-ticket "+customer_id)

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

        convo = await create_ticket_conversation(session=session, last_message_id=last_message_id,ticket=ticket)
        ticket.conversation_id = convo.id
        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)
        return ticket.model_dump(mode='json')
    except Exception:
        logger.error("Gemini agent couldn't create ticket!!!",exc_info=True)
        return "Couldn't create ticket"
