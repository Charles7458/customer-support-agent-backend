from database import SessionDep
from pydantic import BaseModel
from models import Users
from sqlmodel import func, select
from fastapi import APIRouter, Response, Cookie, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
from pwdlib import PasswordHash
import os
from dotenv import load_dotenv
import jwt
import uuid
import random
from enum import Enum
from config import logger

load_dotenv()

router = APIRouter(prefix="/auth")

access_token_expire_minutes = 120
secret_key = os.getenv("SECRET_KEY")
cookie_name = "support_session"
password_hash = PasswordHash.recommended()
ALGORITHM = os.getenv("ALGORITHM")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SUPPORT_SECRET = os.getenv("SUPPORT_SECRET")


class UserRole(str, Enum):
    CUSTOMER = "CUSTOMER"
    SUPPORT_AGENT = "SUPPORT_AGENT"
    ADMIN = "ADMIN"

class SignUpForm(BaseModel):
    full_name: str
    email: str
    password: str
    agree_to_terms: bool = False
    remember_me: bool = False
    model_config = {"extra" : "forbid"}

class LoginForm(BaseModel):
    email: str
    password: str
    remember_me: bool = False
    model_config = {"extra" : "forbid"}

class UserData(BaseModel):#Sent to the frontend. All variables in frontend are camelCase
    fullName: str
    email: str
    role: str

class TokenData(BaseModel):
    full_name: str
    uuid: uuid.UUID
    email:str
    role: str

class SupportLogin(LoginForm):
    support_secret: str

class SupportSignup(SignUpForm):
    support_secret: str

def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(token_data: TokenData, expires_delta: timedelta | None = None):
    payload = {
        "sub": str(token_data.uuid),
        "full_name": token_data.full_name,
        "email": token_data.email,
        "role": token_data.role
    }
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=access_token_expire_minutes)

    expire_timestamp = int(expire.timestamp())

    payload.update({"exp": expire_timestamp})

    access_token = jwt.encode(payload=payload, key=secret_key, algorithm=ALGORITHM)


    return access_token



async def authenticate_user(login:LoginForm, session: SessionDep) -> TokenData:
    try:
        result = await session.exec(select(Users).where(Users.email == login.email))
        user = result.one()
        if not user:
            return None
        if verify_password(login.password, user.password_hash):
            return TokenData(full_name=user.full_name, uuid=user.id, email=user.email,role=user.user_role)
        print("wrong password")
        return None
    except Exception:
        logger.error("User authentication failed",exc_info=True)
        return None
    
def get_hashed_password(password:str):
    return password_hash.hash(password)

async def get_uuid(support_session: str = Cookie(None)) -> str:
    if support_session is None:
        print("Cookie not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication cookie missing. Please log in."
        )
    try:
        user_data = jwt.decode(support_session, secret_key, algorithms=[ALGORITHM])
        current_time = int(datetime.now(timezone.utc).timestamp())

        if user_data.get("exp") and current_time > user_data.get("exp"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired. Please log in."
            )

        return user_data.get("sub")
    
    except Exception as e:
        logger.error("Get uuid failed", exc_info=True)
        print(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or corrupted session token. Please log in."
        )

#Send user's details when requested with cookie having jwt token
@router.get("/me")
def get_current_user(support_session: str = Cookie(None)):
    # 1. Check if the browser actually sent the cookie
    if support_session is None:
        print("Cookie not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication cookie missing. Please log in."
        )
    try:
        user_data = jwt.decode(support_session, secret_key, algorithms=[ALGORITHM])
        
        # 3. Return the private data safely parsed out of the token
        print(user_data)
        current_time = int(datetime.now(timezone.utc).timestamp())

        if user_data.get("exp") and current_time > user_data.get("exp"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired. Please log in."
            )

        user = UserData(fullName=user_data.get("full_name"),email=user_data.get("email"),role=user_data.get("role"))
        return {"user": user}

        
    except Exception:
        # If the token was tampered with, expired, or encrypted with a different key
        logger.error("Get current user failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or corrupted session token."
        )

#Sign up the user insert details in database and send a secure JWE cookie
@router.post("/signup", status_code=200)
async def signup(user: SignUpForm, response:Response, session: SessionDep):
    if not user.agree_to_terms:
        response.status_code = status.HTTP_403_FORBIDDEN
        return {"message": "Not agreed to terms"}
    
    try:
        res = await session.exec(select(func.count()).select_from(Users).where(Users.email == user.email))
        count = res.one()
        #if email already exists
        if(count > 0):
            response.status_code = status.HTTP_409_CONFLICT
            return {"message": "Account with email already exists"}
        
        hashed_password = get_hashed_password(user.password)


        user1 = Users(full_name=user.full_name,email=user.email,password_hash=hashed_password,user_role=UserRole.CUSTOMER)
        print(user1)
        #Inserting user into the users table
        session.add(user1)
        await session.commit()
        await session.refresh(user1)

        token_data = TokenData(full_name=user1.full_name, uuid=user1.id, email=user1.email, role=user1.user_role)

        access_token = create_access_token(token_data)
        age = 3600
        if user.remember_me:
            print("Remeber for 30 days")
            age *= 24*30


        response.set_cookie(
            key=cookie_name,
            value=access_token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=3600,
            path="/"
        )

        user = UserData(fullName=user1.full_name, email=user1.email, role=user1.user_role)

        return {"message": "Successful", "user": user}
    
    except Exception:
        logger.error("Signup failed",exc_info=True)
        response.status_code = 500
        return {"message": "Server Error"}
    
#Login User and send JWE token as a secure cookie
@router.post("/login", status_code=200)
async def login(loginForm: LoginForm, response: Response, session:SessionDep):
    #user's name stored in result if user is authenticated
    token_data = await authenticate_user(loginForm, session)

    if not token_data:
        print("authenticate failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    else:
        #anyone who logs in the normal login is a customer
        token_data.role = 'CUSTOMER'
        access_token = create_access_token(token_data)
        age = 3600
        if loginForm.remember_me:
            print("Remeber for 30 days")
            age *= 24*30

        response.set_cookie(
            key=cookie_name,
            value=access_token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=age,
            path="/"
        )

        user = UserData(fullName= token_data.full_name, email= token_data.email, role = token_data.role)

        return {"message": "Successful", "user": user}


@router.post("/logout")
def logout(response: Response):
    """
    Clears the session cookie from the user's browser.
    """
    response.delete_cookie(key=cookie_name,samesite="none", path="/")
    return {"message": "Logged out successfully."}


@router.delete("/del-acc")
async def del_account(session:SessionDep, response:Response, support_session:str = Cookie(None)):
    user_uuid = await get_uuid(support_session=support_session)
    anonymized_acc_name = "deleted_"+ str(random.randrange(1,10000000))
    anonymized_email = anonymized_acc_name + "@gmail.com"
    result = await session.exec(select(Users).where(Users.id == user_uuid))
    
    user1 = result.one() #.values(full_name=anonymized_acc_name, email=anonymized_email), is_deleted=True)
    user1.full_name = anonymized_acc_name
    user1.email = anonymized_email
    user1.is_deleted = True
    session.add(user1)
    await session.commit()
    await session.refresh(user1)
    print(user1)
    response.delete_cookie(key=cookie_name, path="/")
    return {"message": "Account deleted successfully."}


@router.post("/support/signup")
async def support_signup(user:SupportSignup, response:Response, session:SessionDep):
    if user.support_secret != SUPPORT_SECRET:
        print("authenticate failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.agree_to_terms:
        response.status_code = status.HTTP_403_FORBIDDEN
        return {"message": "Not agreed to terms"}
    
    try:
        res = await session.exec(select(func.count()).select_from(Users).where(Users.email == user.email))
        count = res.one()
        #if email already exists
        if(count > 0):
            response.status_code = status.HTTP_409_CONFLICT
            return {"message": "Account with email already exists"}
        
        hashed_password = get_hashed_password(user.password)


        user1 = Users(full_name=user.full_name,email=user.email,password_hash=hashed_password,user_role=UserRole.SUPPORT_AGENT)
        print(user1)
        #Inserting user into the users table
        session.add(user1)
        await session.commit()
        await session.refresh(user1)

        token_data = TokenData(full_name=user1.full_name, uuid=user1.id, email=user1.email, role=user1.user_role)

        access_token = create_access_token(token_data)
        age = 3600
        if user.remember_me:
            print("Remeber for 30 days")
            age *= 24*30


        response.set_cookie(
            key=cookie_name,
            value=access_token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=3600,
            path="/"
        )

        user = UserData(fullName=user1.full_name, email=user1.email, role=user1.user_role)

        return {"message": "Successful", "user": user}
    
    except Exception:
        logger.error("Support Signup Failed", exc_info=True)
        response.status_code = 500
        return {"message": "Server Error"}

@router.post("/support/login")
async def support_login(form:SupportLogin, response:Response, session:SessionDep):
    if form.support_secret != SUPPORT_SECRET:
        print("authenticate failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    loginForm = LoginForm(email=form.email, password=form.password, remember_me=form.remember_me)
    token_data = await authenticate_user(loginForm, session)

    if not token_data:
        print("authenticate failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    else:
        access_token = create_access_token(token_data)
        age = 3600
        if loginForm.remember_me:
            print("Remeber for 30 days")
            age *= 24*30

        response.set_cookie(
            key=cookie_name,
            value=access_token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=age,
            path="/"
        )

        user = UserData(fullName= token_data.full_name, email= token_data.email, role = token_data.role)

        return {"message": "Successful", "user": user}