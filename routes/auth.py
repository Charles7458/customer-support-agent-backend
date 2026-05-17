from ..database import SessionDep
from pydantic import BaseModel
from ..models import Users
from sqlmodel import col, func, select
from fastapi import APIRouter, Form, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from datetime import datetime, timedelta, timezone
from pwdlib import PasswordHash
import os
from dotenv import load_dotenv
import jwt
from jwt.exceptions import InvalidTokenError

load_dotenv()

router = APIRouter(prefix="/auth")

access_token_expire_minutes = 120
secret_key = os.getenv("SECRET_KEY")
password_hash = PasswordHash.recommended()
algorithm = os.getenv("ALGORITHM")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class SignUpForm(BaseModel):
    full_name: str
    email: str
    password: str
    model_config = {"extra" : "forbid"}

class LoginForm(BaseModel):
    email: str
    password: str
    model_config = {"extra" : "forbid"}

class Token(BaseModel):
    access_token: str
    token_type: str



def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt



@router.post("/signup", status_code=200)
async def signup(user: Annotated[SignUpForm, Form()],response:Response, session: SessionDep): # type: ignore
    try:
        count = session.exec(select(func.count()).select_from(Users).where(Users.email == user.email)).one()
        #if email already exists
        if(count > 0):
            response.status_code = status.HTTP_409_CONFLICT
            return None

        hashed_password = password_hash.hash(user.password)

        user1 = Users(full_name=user.full_name,email=user.email,password_hash=hashed_password)

        #Inserting user into the users table
        session.add(user1)
        session.commit()

        access_token_expires = timedelta(minutes=access_token_expire_minutes)

        access_token = create_access_token(
        data={"sub": user.full_name}, expires_delta=access_token_expires
        )

        return Token(access_token=access_token, token_type="bearer")
    
    except Exception as e:
        print(e)
        response.status_code = 500
        return None

@router.post("/login", status_code=200)
async def login():
    pass