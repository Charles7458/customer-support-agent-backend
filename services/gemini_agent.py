from google import genai
from google.genai import types
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from .tools import get_faq_declaration, get_order_declaration, create_ticket_declaration
from ..models import Tracking, OrderCard, Content, ChatMessages, ChatHistoryResponse, UserRole


load_dotenv()


response_json_schema = {
    "$schema" : "https://json-schema.org/draft/2020-12/schema",
    "$id" : "https://example.com/response.schema.json",
    "title": "Response",
    "description": "Response to the user's query.",
    "type" : "object",
    "properties" : {
        "text" : {
            "type": "string",
            "description" : "Text content of the message."
        },
        "tracking" : {
            "type" : "object",
            "description" : "Object containing tracking id and carrier name of an order. Optional, added if user wants to know the staus of an order or track an order.",
            "properties" : {
                "tracking_id" : {
                    "type" : "string",
                    "description" : "tracking id of the order"
                },
                "carrier" : {
                    "type" : "string",
                    "description" : "Name of the carrier of the order. example: 'UPS' "
                }
            }
        },
        "order_card" : {
            "type" : "object",
            "description" : "Object containing order id and status. Added if user wants information on an order.",
            "properties" : {
                "order_id": {
                    "type" : "string",
                    "description" : "ID of the corresponding order"
                },
                "status" : {
                    "enum" : ["Ordered", "Packed", "Shipped", "Out for Delivery", "Delivered"],
                    "description": "Status of the order."
                }
            }
        },
        "bullet_list": {
            "type" : "array",
            "items" : {"type" : "string"},
            "description" : "Strings displayed as bullet points in chat. Add inference/ operational steps or order transit statuses as bullet points."
        }
    },
    "required" : ["text"]
}

gemini_api_key = os.getenv("GEMINI_API_KEY")
model = 'gemini-3.1-flash-lite'

client = genai.Client(api_key=gemini_api_key)

tools = types.Tool(function_declarations=[get_faq_declaration, get_order_declaration, create_ticket_declaration])

tool_routing_config = types.GenerateContentConfig(
    tools=[tools],
    # Do NOT include response_json_schema here
)

# 2. Configuration strictly for forced JSON formatting on the final reply
final_json_formatting_config = types.GenerateContentConfig(
    response_mime_type="application/json", # Forces JSON mode explicitly
    response_json_schema=response_json_schema
)

def get_content(prompt:str):
    contents = [
        types.Content(
            role="user", parts=[types.Part(text=prompt)]
        )
    ]
    return contents

def get_final_response_content(contents:list[types.Content], model_response:str, tool_call:dict[str,any], result):
    function_response_part = types.Part.from_function_response(
            name=tool_call['name'],
            response={"result": result}
        )
    # Append function call and result of the function execution to contents
    contents.append(model_response) # Append the content from the model's response.
    contents.append(types.Content(role="user", parts=[function_response_part])) # Append the function response
    return contents