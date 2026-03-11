import hashlib

from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel, EmailStr, Field
from db.database import get_db
from db.models import UserRecord

router = APIRouter(prefix="/auth", tags=["auth"])

class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(min_length=5, max_length=20)
    avatar_url: str = Field(default="")
    password: str = Field(min_length=8, max_length=20)



@router.post("/login")
def login():
    pass

@router.post("/signup")
def signup(user_create: UserCreate, db = Depends(get_db)):
    hash_password = hashlib.sha256(user_create.password.encode()).hexdigest()

    new_user = UserRecord(
        email = user_create.email,
        name = user_create.name,
        avatar_url = user_create.avatar_url,
        password_hash = hash_password
    )
    
    db.add(new_user)
    db.commit()
    return (user_create)