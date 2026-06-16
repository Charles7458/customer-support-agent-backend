
from fastapi import APIRouter
from ..models import Faqs
from ..database import SessionDep

router = APIRouter(prefix="/faq")



@router.post("/")
async def add_faq(faq:Faqs, session: SessionDep):
    session.add(faq)
    await session.commit()
    await session.refresh(faq)
    return faq