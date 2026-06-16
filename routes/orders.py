from ..database import SessionDep
from ..models import  Orders, Tracking
from fastapi import APIRouter
import nanoid
from datetime import datetime

router = APIRouter(prefix="/orders")

@router.post("/")
async def create_order(orders: list[Orders], session:SessionDep):
    for order in orders:
        if isinstance(order.order_date, str):
            # fromisoformat handles the "2026-04-12T16:40:00Z" format perfectly
            order.order_date = datetime.fromisoformat(order.order_date.replace("Z", "+00:00"))
        order.tracking_id = f"TRK-{nanoid.generate(size=6)}"
        session.add(order)
    await session.commit()

@router.post("/tracking")
async def create_tracking_update(tracking: list[Tracking], session:SessionDep):
    for t in tracking:
        if isinstance(t.updated_at, str):
            # fromisoformat handles the "2026-04-12T16:40:00Z" format perfectly
            t.updated_at = datetime.fromisoformat(t.updated_at.replace("Z", "+00:00"))
        session.add(t)
    await session.commit()
