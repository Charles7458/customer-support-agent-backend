from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
from .tools import get_faq_declaration, get_order_declaration, create_ticket_declaration
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")
model = 'gemini-2.5-flash-lite'

client = genai.Client(api_key=gemini_api_key)

tools = types.Tool(function_declarations=[get_faq_declaration, get_order_declaration, create_ticket_declaration])

config = types.GenerateContentConfig(tools=[tools])

def get_content(prompt:str):
    contents = [
        types.Content(
            role="user", parts=[types.Part(text=prompt)]
        )
    ]
    return contents

def get_final_response_content(contents:list[types.Content], model_response:str, tool_call:dict[str,any], result) -> str:
    function_response_part = types.Part.from_function_response(
            name=tool_call['name'],
            response={"result": result}
        )
    # Append function call and result of the function execution to contents
    contents.append(model_response) # Append the content from the model's response.
    contents.append(types.Content(role="user", parts=[function_response_part])) # Append the function response
    return contents