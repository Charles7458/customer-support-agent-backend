from ..database import SessionDep
from pydantic import BaseModel
from fastapi import APIRouter, Cookie, status, HTTPException, Response
from ..models import Users
from sqlmodel import select, func
from .auth import authenticate_user, LoginForm, get_current_user, get_uuid, get_hashed_password, create_access_token, cookie_name, TokenData, UserData


class PswdUpdateForm(BaseModel):
    currentPassword:str
    newPassword:str

class EmailUpdateForm(BaseModel):
    password:str
    newEmail:str

class NameUpdateForm(BaseModel):
    newName:str

router = APIRouter(prefix="/users")

@router.put("/update-name")
async def update_details(updateForm:NameUpdateForm, session:SessionDep,response:Response, support_session:str = Cookie(None)):

    user_uuid = await get_uuid(support_session=support_session)

    user1 = session.exec(select(Users).where(Users.user_id==user_uuid)).one()
    user1.full_name = updateForm.newName
    session.add(user1)
    session.commit()
    session.refresh(user1)

    access_token = create_access_token(token_data=TokenData(full_name=user1.full_name,uuid=user1.user_id,email=user1.email,role=user1.email))
    age = 3600
    response.set_cookie(
            key=cookie_name,
            value=access_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=age,
            path="/"
        )

@router.put("/update-email")
async def update_email(updateForm:EmailUpdateForm, session:SessionDep, response:Response, support_session:str = Cookie(None)):
    res = get_current_user(support_session=support_session)
    print("inside")
    print(res)
    user_data = res["user"]
    credentials = LoginForm(email = user_data.email,password=updateForm.password)
    user = authenticate_user(login = credentials, session=session)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    else:
        # check if email associated with another account
        count = session.exec(select(func.count()).select_from(Users).where(Users.email == updateForm.newEmail)).one()
        if(count > 0):
            raise HTTPException(
                status_code = status.HTTP_409_CONFLICT,
                detail="Email already associated with another account"
            )
        user1 = session.exec(select(Users).where(Users.user_id == user.uuid)).one()
        user1.email = updateForm.newEmail
        session.add(user1)
        session.commit()

        session.refresh(user1)

        access_token = create_access_token(token_data=TokenData(full_name=user1.full_name,uuid=user1.user_id,email=user1.email,role=user1.email))
        age = 3600
        response.set_cookie(
                key=cookie_name,
                value=access_token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=age,
                path="/"
            )


@router.put("/update-pswd")
async def update_password(updateForm:PswdUpdateForm, session:SessionDep, support_session:str = Cookie(None)):

    res = get_current_user(support_session=support_session)
    user_data = res["user"]
    credentials = LoginForm(email=user_data.email, password=updateForm.currentPassword)
    user = authenticate_user(login=credentials, session=session)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    else:
        hashed_password = get_hashed_password(updateForm.newPassword)
        user1 = session.exec(select(Users).where(Users.user_id == user.uuid)).one()
        user1.password_hash = hashed_password
        session.add(user1)
        session.commit()

