from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Cookie
from ..services.prompt import redact_pii
from ..services.orchestrate import generate_response
from ..database import SessionDep

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

@router.get("/redact")
def redact_chat(text:str):
    return redact_pii(text)

@router.get("/")
async def get_chats(conv_id:str):
    pass
    


@router.websocket("/ws")
async def chat_ws_endpoint(websocket:WebSocket,session:SessionDep, support_session:str = Cookie(None)):
    await websocket.accept()
    try:    
        if(support_session is None):
            print("Cookie not found")
        while True:
            data: dict[str,str] = await websocket.receive_json()
            message = data["content"]
            print(message)
            print(support_session)

            output = await generate_response(text=message, session=session, support_session=support_session)
            
            print(output)
            await websocket.send_json(
                {
                    "type": "chat_message",
                    "role":"AI",
                    "content": output
                })
    
    except WebSocketDisconnect:
        print("Client Disconnected")
        
        
        