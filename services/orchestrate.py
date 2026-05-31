
from .gemini_agent import client,model,config, get_content, get_final_response_content
from .prompt import generate_prompt
from .tools import get_faqs, get_orders, create_a_ticket
from ..routes.auth import get_uuid
from ..database import SessionDep


async def generate_response(text:str, session:SessionDep, support_session:str):

    uuid = await get_uuid(support_session)

    prompt = generate_prompt(text)

    contents = get_content(prompt)

    response = client.models.generate_content(
        model=model,
        contents= contents,
        config=config
    )

    # Check for a function call
    if response.candidates[0].content.parts[0].function_call:
        function_call = response.candidates[0].content.parts[0].function_call
        print(f"Function to call: {function_call.name}")
        print(f"ID: {function_call.id}")
        print(f"Arguments: {function_call.args}")

        result:any
        #  Call appropriate function:
        if function_call.name == "get_faqs":
            result = get_faqs(keywords = function_call.args["keywords"], session=session)
        elif function_call.name == "get_orders":
            result = get_orders(user_id=uuid)
        elif function_call.name == "create_a_ticket":
            result = create_a_ticket(user_id=uuid, issue=function_call.args["issue"],priority=function_call.args["priority"], session=session)
        
        # Create a function response part
        tool_call = {
            "name": function_call.name,
            "id": function_call.id
        }

        final_response_content = get_final_response_content(contents=contents,model_response= response.candidates[0].content,tool_call=tool_call, result=result)

        final_response = client.models.generate_content(
            model=model,
            config=config,
            contents=final_response_content,
        )

        return final_response.text