
from fastapi import APIRouter, Cookie, HTTPException, status
from models import Faqs
from database import SessionDep
from routes.auth import get_current_user

router = APIRouter(prefix="/faq")



@router.post("/insert")
async def add_faq(faq:Faqs, session: SessionDep, support_session:str=Cookie(None)):
    role = get_current_user(support_session=support_session)["user"].role
    if(role != 'SUPPORT_AGENT' and role !='ADMIN'):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not allowed to create faq")
    session.add(faq)
    await session.commit()
    await session.refresh(faq)
    return faq