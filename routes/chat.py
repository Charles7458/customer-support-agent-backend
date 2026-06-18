from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Cookie, HTTPException
from services.prompt import redact_pii
from services.orchestrate import generate_response
from database import SessionDep
from models import Messages, Conversations
from routes.auth import get_uuid
from pydantic import TypeAdapter
from sqlmodel import select
from sqlalchemy.exc import NoResultFound
from services.conversations import create_conversation
from models import Content, ChatMessages, ChatHistoryResponse, UserRole
from config import logger
import json

router = APIRouter(prefix="/chat")


# class ConnectionManager:
#     def __init__(self):
#         self.active_connections : list[WebSocket]
    
#     async def connect(self, websocket:WebSocket):
#         await websocket.accept()
#         self.active_connections.append(websocket)
    
#     def disconnect(self, websocket:WebSocket):
#         self.active_connections.remove(websocket)

#     async def send_message(self, message:str, websocket:WebSocket):
#         await websocket.send_text(message)

#     async def broadcast(self, message:str):
#         for connection in self.active_connections:
#             await connection.send_text(message)

# manager = ConnectionManager()

@router.post("/redact")
def redact_chat(chat:dict[str,str]):
    redacted = redact_pii(chat["input"])
    return redacted

async def store_chat(session:SessionDep, message:ChatMessages, conversation_id: str) -> Messages:
    serializable_content = message.content.model_dump()
    msg1 = Messages(conversation_id=conversation_id,role=message.role,content=serializable_content,sent_at=message.sent_at)
    session.add(msg1)
    await session.commit()
    await session.refresh(msg1)
    return msg1

@router.get("/", response_model=ChatHistoryResponse)
async def get_ai_chat(session:SessionDep,support_session:str = Cookie(None)):
    user_id = await  get_uuid(support_session)
    conversation_id = 'conv-'+user_id
    try:
        convo_res = await session.exec(select(Conversations).where(Conversations.id==conversation_id))
        convo = convo_res.one()
        chats_res = await session.exec(select(Messages.id, Messages.role, Messages.content, Messages.sent_at).select_from(Messages).where(Messages.conversation_id == conversation_id).order_by(Messages.id))
        chats = chats_res.all()
        adapter = TypeAdapter(list[ChatMessages])
        validated_chats = adapter.validate_python(chats, from_attributes=True, by_name=True)
        return {
            "conversation": convo,
            "messages": validated_chats
        }

    except NoResultFound:
        conversation = await create_conversation(session,conversation_id,user_id)
        return {
            "conversation": conversation,
            "messages" : []
        }
    except Exception:
        logger.error("Get AI chat history Failed",exc_info=True)
        raise HTTPException(status_code=404, detail="Chat history not found")
    
    


    


@router.websocket("/ws")
async def ai_chat_endpoint(websocket:WebSocket,session:SessionDep, support_session:str = Cookie(None)):
    await websocket.accept()
    user_id = await get_uuid(support_session=support_session)

    try:    
        if(support_session is None):
            print("Cookie not found")
        while True:
            try:
                await websocket.send_json({
                    "type": "status",
                    "value": "online"
                })

                conversation_id = 'conv-'+user_id

                data: dict[str,str] = await websocket.receive_json()
                # data => {"type": "message", "value": message}
                user_message = data["value"]
                print("user message: ", user_message)

                user_msg = ChatMessages(role=UserRole.CUSTOMER, content=user_message["content"], sent_at=user_message["sent_at"])
                user_message = await store_chat(session, user_msg, conversation_id)
                user_message = ChatMessages(id=user_message.id,role=user_message.role,content=user_message.content,sent_at=user_message.sent_at)
                
                #Send user's message back to frontend
                await websocket.send_json({
                    "type": "message",
                    "value": user_message.model_dump(mode="json")
                })

                await websocket.send_json({
                    "type": "status",
                    "value": "typing"
                })

                output = await generate_response(text=user_message.content.text, user_message_id=user_message.id, conversation_id=conversation_id, session=session, support_session=support_session)

                if output is not None:
                    print(output)
                    ai_msg = ChatMessages(role=UserRole.AI, content=output.model_dump())
                else:
                    ai_msg = ChatMessages(role=UserRole.AI, content = Content(text="Sorry, we ran into a problem while processing your query. Please try again."))

                ai_message = await store_chat(session=session,message=ai_msg,conversation_id=conversation_id)
                chat = ChatMessages(id=ai_message.id,role=ai_message.role,content=ai_message.content,sent_at=ai_message.sent_at)
                print(chat)
                await websocket.send_json({
                    "type": "status",
                    "value": "stopped"
                })
                #Send AI output
                await websocket.send_json({
                    "type": "message",
                    "value":chat.model_dump(mode="json")
                })


    
            except WebSocketDisconnect:
                logger.info("Client Disconnected")
                break

            except Exception as e:
                # Catch logic/database/agent errors
                logger.error(f"Error processing message for {user_id}: {e}", exc_info=True)
                # Send error back to client so UI can react
                await websocket.send_text(json.dumps({"error": "Failed to process message."}))
        
    finally:
        # Cleanup: This runs even if the loop crashes or the client disconnects
        logger.info(f"Cleaning up resources for {user_id}.")
        await websocket.close()


        