from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Cookie, HTTPException, status
from ..database import SessionDep
from .auth import get_uuid, get_current_user
import uuid
from ..models import Conversations, Messages, Content, ChatMessages, UserRole
from sqlmodel import select
from pydantic import BaseModel, TypeAdapter

router = APIRouter(prefix="/support-chat")

class ConvID(BaseModel):
    conversation_id: str

class ConnectionManager:
    def __init__(self):
        self.active_connections : dict[str,WebSocket] = {}

    async def connect(self, id:uuid.UUID | str, socket:WebSocket):
        await socket.accept()
        self.active_connections[str(id)] = socket
        print("active_connections: ", self.active_connections)
    
    def isOnline(self, id: uuid.UUID | str) -> bool:
        return str(id) in self.active_connections
    
    def find(self, id: uuid.UUID | str) -> WebSocket | None:
        # try:
            socket = self.active_connections.get(str(id))
            return socket
        # except KeyError:
        #     return None
        
    async def send_message(self, other_id:uuid.UUID | str, message:ChatMessages):
        other_socket = self.find(other_id)
        if other_socket:
            await other_socket.send_json({
                "type": "message",
                "value": message.model_dump(mode='json')
            })
    
    async def send_status(self, other_id:uuid.UUID |str, user_status: str):
        other_socket = self.find(other_id)
        if other_socket:
            await other_socket.send_json({
                        "type": "status",
                        "value": user_status
                    })
    
    def disconnect(self, id: uuid.UUID | str):
        self.active_connections.pop(str(id))


manager = ConnectionManager()

@router.websocket("/ws/{conversation_id}")
async def support_chat(conversation_id:str, websocket:WebSocket, session:SessionDep, support_session:str = Cookie(None)):
    id = await get_uuid(support_session)
    await manager.connect(id,websocket)
    role = get_current_user(support_session)["user"].role
    other_id = ""
    try:
        while True:
            print("Received conv-id:", conversation_id)
                
            if(role=="CUSTOMER"):
                print("customer is online")
                other_id = session.exec(select(Conversations.agent_id).where(Conversations.id==conversation_id)).one()
            else:
                print("agent is online")
                other_id = session.exec(select(Conversations.customer_id).where(Conversations.id == conversation_id)).one()
            print("other id:",other_id)
            # sending the other person's online status
            online_status = "online" if(manager.isOnline(other_id)) else "offline"
            print("other person is", online_status)
            await websocket.send_json({
                "type":"status",
                "value": online_status
            })
            #notifying the other person that this person is online, if the other person is also online
            if(online_status=="online"):
                await manager.send_status(other_id, "online")

            data = await websocket.receive_json()
            print(data)
            #Send status updates to the other person
            if data["type"] == "status":
                await manager.send_status(other_id, data["value"])

            elif data["type"] == "message":
                user_message = data["value"]
                message = Messages(conversation_id=conversation_id,role=user_message["role"], content=user_message["content"], sent_at=user_message["sent_at"])
                session.add(message)
                session.commit()
                session.refresh(message)
                chat = ChatMessages(id=message.id,role=message.role,content=message.content,sent_at=message.sent_at)
                print(chat)
                #Send message back to the sender
                await websocket.send_json({
                    "type": "message",
                    "value": chat.model_dump(mode="json")
                })
                #Send message to the receiver
                await manager.send_message(other_id,chat)

            

    except WebSocketDisconnect:
        manager.disconnect(id)
        manager.send_status(other_id, "offline")


@router.post("/")
async def fetch_support_chat(convID:ConvID,session:SessionDep, support_session:str = Cookie(None)):
    if not convID.conversation_id:
        print("support chat needs conv id")
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Conversation ID needed")

    try:

        convo = session.exec(select(Conversations).where(Conversations.id==convID.conversation_id)).one()
        chats = session.exec(select(Messages.id, Messages.role, Messages.content, Messages.sent_at).select_from(Messages).where(Messages.conversation_id == convID.conversation_id).order_by(Messages.id)).all()
        adapter = TypeAdapter(list[ChatMessages])
        validated_chats = adapter.validate_python(chats, from_attributes=True, by_name=True)
        return {
            "conversation": convo,
            "messages": validated_chats
        }
    
    except Exception as e:
        print(e)
        raise HTTPException(status_code=404, detail="Chat history not found")

    
