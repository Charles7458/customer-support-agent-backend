from ..database import SessionDep
from pydantic import BaseModel
from ..models import Users
from sqlmodel import col, func, select
from fastapi import APIRouter, Form, Response, Cookie, status, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from datetime import datetime, timedelta, timezone
from pwdlib import PasswordHash
import os
from dotenv import load_dotenv
from jwt.exceptions import InvalidTokenError
from authlib.jose import JsonWebEncryption
import json

load_dotenv()

router = APIRouter(prefix="/auth")

access_token_expire_minutes = 120
secret_key = os.getenv("SECRET_KEY")
cookie_name = "support_session"
password_hash = PasswordHash.recommended()
ALGORITHM = os.getenv("ALGORITHM")
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


class TokenData(BaseModel):
    full_name: str
    email: str



def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(token_data: TokenData, expires_delta: timedelta | None = None):
    payload = {
        "sub": token_data.full_name,
        "email": token_data.email
    }
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=access_token_expire_minutes)

    payload.update({"exp": expire})
    payload_bytes = json.dumps(payload).encode("utf-8")
    protected_header = {'alg': 'dir', 'enc': 'A256GCM'}
    jwe_token = JsonWebEncryption.serialize_compact(protected_header, payload_bytes, secret_key)

    return jwe_token


def get_current_user(token:str):
    try:
        # 2. Decrypt the JWE token locally
        _, decrypted_bytes = JsonWebEncryption.deserialize_compact(token, secret_key)
        user_data = json.loads(decrypted_bytes.decode("utf-8"))
        
        # 3. Return the private data safely parsed out of the token
        return {
            "authenticated": True,
            "user_id": user_data.get("sub"),
            "email": user_data.get("email"),
            "role": user_data.get("role")
        }
        
    except Exception:
        # If the token was tampered with, expired, or encrypted with a different key
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or corrupted session token."
        )


def authenticate_user(login:LoginForm, session: SessionDep) -> TokenData:
    user = session.exec(select(Users).where(Users.email == login.email)).one()
    if not user:
        return None
    if verify_password(login.password, user.password_hash):
        return TokenData(user.full_name, user.email)
    return None



@router.post("/signup", status_code=200)
async def signup(user: Annotated[SignUpForm, Form()],response:Response, session: SessionDep): # type: ignore
    try:
        count = session.exec(select(func.count()).select_from(Users).where(Users.email == user.email)).one()
        #if email already exists
        if(count > 0):
            response.status_code = status.HTTP_409_CONFLICT
            return {"message": "Account with email already exists"}

        hashed_password = password_hash.hash(user.password)

        user1 = Users(full_name=user.full_name,email=user.email,password_hash=hashed_password)

        #Inserting user into the users table
        session.add(user1)
        session.commit()

        token_data = TokenData(user1.full_name, user1.email)

        access_token = create_access_token(token_data)

        response.set_cookie(
            key=cookie_name,
            value=access_token.decode("utf-8"),
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=3600,
            path="/"
        )

        return {"message": "Signup and Login successful"}
    
    except Exception as e:
        print(e)
        response.status_code = 500
        return {"message": "Server Error"}

@router.post("/login", status_code=200)
async def login(loginForm: Annotated[LoginForm, Form()] | None, response: Response, session:SessionDep, support_session: str = Cookie(None)):
    #user's name stored in result if user is authenticated
    token_data = authenticate_user(loginForm, session)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    else:
        access_token = create_access_token(token_data)

        response.set_cookie(
            key=cookie_name,
            value=access_token.decode("utf-8"),
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=3600,
            path="/"
        )

        return {"message": "Signup and Login successful"}


@router.post("/logout")
def logout(response: Response):
    """
    Clears the session cookie from the user's browser.
    """
    response.delete_cookie(key=cookie_name, path="/")
    return {"message": "Logged out successfully."}