import os
from dotenv import load_dotenv
from sqlmodel import create_engine, Session
from fastapi import Depends
from typing import Annotated


load_dotenv()

db_url = os.getenv("database_url")

engine = create_engine(db_url, echo=True)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session,Depends(get_session)]