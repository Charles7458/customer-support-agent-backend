from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
import os
import time
from dotenv import load_dotenv
from routes.auth import router as auth_router
from routes.users import router as user_router
from routes.chat import router as chat_router
from routes.tickets import router as ticket_router
from routes.support_chat import router as support_chat_router
from routes.orders import router as order_router
from routes.faq import router as faq_router
from health import router as health_router
from config import logger

load_dotenv()

app = FastAPI()

app.include_router(auth_router)
app.include_router(user_router)
app.include_router(chat_router)
app.include_router(ticket_router)
app.include_router(support_chat_router)
app.include_router(order_router)
app.include_router(faq_router)
app.include_router(health_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL")],  # your frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_url = os.getenv("ASYNC_DB_URL")

engine = create_async_engine(db_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@app.middleware("http")
async def add_response_time_recorder(request: Request, call_next):
    # Record the start time before the route executes
    start_time = time.perf_counter()
    
    # Process the request and wait for the response
    response = await call_next(request)
    
    # Calculate total execution time (in seconds)
    process_time = time.perf_counter() - start_time
    
    # Format it cleanly (e.g., convert to milliseconds or keep as seconds)
    duration_ms = round(process_time * 1000, 2)
    
    # Log it to your Render or console stream (you can route this to monitoring later)
    logger.info(f"Endpoint: {request.url.path} | Method: {request.method} | Duration: {duration_ms}ms")
    
    # Optionally attach the timing header so you can inspect it in your frontend network tab
    response.headers["X-Process-Time"] = f"{duration_ms}ms"
    
    return response
