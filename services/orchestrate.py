
from .gemini_agent import client,model,tool_routing_config, final_json_formatting_config, get_function_response_part
from google.genai import types
from .prompt import generate_prompt, generate_message_prompt
from .tools import get_faqs, get_recent_orders, get_orders_by_month, get_order_by_id, get_tracking_updates, create_a_ticket
from ..routes.auth import get_uuid
from ..database import SessionDep
import json
from ..models import Content, Messages
from fastapi import Cookie
from functools import partial

from sqlalchemy import select, desc
from ..config import logger

async def get_conversation_history(conversation_id: str, session: SessionDep, limit: int = 3):
    # Fetch the last N messages for the conversation

    result = await session.exec(select(Messages.content, Messages.role).select_from(Messages).where(Messages.conversation_id == conversation_id).order_by(desc(Messages.sent_at)).limit(limit))
    messages = result.all()
    print(messages)
    # Reverse to get chronological order (oldest to newest)
    return list(reversed(messages))

async def execute_tool_by_name(name: str, user_message_id:int, args:dict[str,str], session:SessionDep, support_session:str = Cookie(None)):
    tools = {
        "get_faqs": get_faqs,
        "get_recent_orders": get_recent_orders,
        "get_order_by_month": get_orders_by_month,
        "get_order_by_id": get_order_by_id,
        "get_tracking_updates": get_tracking_updates,
        "create_a_ticket": partial(create_a_ticket, last_message_id=user_message_id)
    }
    tool_func = tools.get(name)
    try:
        response = await tool_func(**args, session=session, support_session=support_session)
        return response
    except Exception as e:
        print(e)
        logger.error("Agent Failed to call tool: "+name, exc_info=True)
        return name+" function call failed"


async def generate_response(text:str, user_message_id:int, conversation_id: str, session:SessionDep, support_session:str = Cookie(None)) -> Content:

    user_id =  await get_uuid(support_session)
    print("uuid from orchestrate"+user_id)

    history = []
    recent_messages = await get_conversation_history(conversation_id, session)
    for msg in recent_messages:
        role = "model" if msg.role == "AI" else "user"
        history.append(types.Content(
            role=role, parts=[types.Part(text=msg.content["text"])]
        ))

    prompt = generate_prompt(text)

    history.append(types.Content(
            role="user", parts=[types.Part(text=prompt)]
        ))
    
    max_steps = 5
    step = 0

    while step < max_steps:
        #generate response
        response = client.models.generate_content(
            model=model,
            contents= history,
            config=tool_routing_config
        )

        # append response to history so the AI knows what it did
        history.append(response.candidates[0].content)

        function_call = response.candidates[0].content.parts[0].function_call

        # Return model's response if there's no function call
        if not function_call:
            final_response = client.models.generate_content(
            model=model,
            config=final_json_formatting_config,
            contents=history,
            )
            print("final_response: \n",final_response.text)
            raw_json_str =  final_response.text
            print(raw_json_str)
            response_dict = json.loads(raw_json_str)
            return Content(**response_dict)

        print(f"Function to call: {function_call.name}")
        print(f"ID: {function_call.id}")
        print(f"Arguments: {function_call.args}")
        # result:any
        # #  Call appropriate function:
        # if function_call.name == "get_faqs":
        #     result = await get_faqs(keywords = function_call.args["keywords"], session=session)
        # elif function_call.name == "get_recent_orders":
        #     result = await get_recent_orders(user_id=user_id)
        # elif function_call.name == "get_order_by_month":
        #     result = await get_orders_by_month(month=function_call.args["month"], year=function_call.args["year"])
        # elif function_call.name == "get_order_by_id":
        #     result = await get_order_by_id(order_id=function_call.args["order_id"])
        # elif function_call.name == "get_tracking_updates":
        #     result = await get_tracking_updates(order_id=function_call.args["order_id"])
        # elif function_call.name == "create_a_ticket":
        #     result = await create_a_ticket(issue=function_call.args["issue"],last_message_id=user_message_id, priority=function_call.args["priority"], session=session, support_session=support_session)
        
        result = await execute_tool_by_name(
            name = function_call.name,
            user_message_id = user_message_id,
            args = function_call.args,
            session = session,
            support_session = support_session
        )
        # Create a function response part
        tool_call = {
            "name": function_call.name,
            "id": function_call.id
        }
        # history = get_final_response_content(contents=history,model_response= response.candidates[0].content,tool_call=tool_call, result=result)
        # final_response = client.models.generate_content(
        #     model=model,
        #     config=final_json_formatting_config,
        #     contents=history,
        # )
        
        # 5. Add the tool result back to history
        # This is the "Agentic" part: The AI now sees the result as part of the context
        history.append({
            "role": "function",
            "parts": get_function_response_part(tool_call=tool_call, result=result)
        })

        step+=1

            
    return Content(text="Agent reached maximum steps without resolution")
    
async def generate_message_response(prompt:str,message:str, role:str):
    content = types.Content(
            role="user", parts=[types.Part(text=generate_message_prompt(prompt, message, role))]
        )
    
    #generate response
    response = client.models.generate_content(
            model=model,
            contents= content
        )

    return response.text