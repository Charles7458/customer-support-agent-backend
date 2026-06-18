from database import SessionDep
from models import  Orders, Tracking, Users
from fastapi import APIRouter, Cookie, HTTPException, status
from sqlmodel import select
import nanoid
from config import logger
from routes.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/orders")

class OrderRequest(BaseModel):
    customer_email: str
    product_name: str
    amount: int
    status: str

class TrackingRequest(BaseModel):
    order_id:str
    carrier:str
    updates:str
    status:str


@router.post("/insert")
async def create_order(order: OrderRequest, session:SessionDep, support_session:str=Cookie(None)):
    role = get_current_user(support_session=support_session)["user"].role
    if(role != 'SUPPORT_AGENT' and role !='ADMIN'):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not allowed to create faq")

    try:
        res = session.exec(select(Users.id).where(Users.email==order.customer_email))
        customer_id = res.one()
        tracking_id = f"TRK-{nanoid.generate(size="6")}"
        order1 = Orders(customer_id=customer_id,product_name=order.product_name,amount=order.amount,tracking_id=tracking_id,status=order.status)
        session.add(order1)
        await session.commit()

    except Exception as e:
        print(e)
        logger.error("Create order failed", exc_info=True)


@router.post("/tracking/insert")
async def create_tracking_update(tracking: TrackingRequest, session:SessionDep, support_session:str = Cookie(None)):

    role = get_current_user(support_session=support_session)["user"].role
    if(role != 'SUPPORT_AGENT' and role !='ADMIN'):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not allowed to create faq")

    try:
        session.add(tracking)
        await session.commit()

    except Exception as e:
        print(e)
        logger.error("Tracking update insertion failed", exc_info=True)
