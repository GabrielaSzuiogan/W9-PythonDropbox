import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from db.database import get_db
from db.models import UserRecord
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from api.routes.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

password_hash = PasswordHash((Argon2Hasher(),))
# takes the password a user types and turns it into a long, scrambled string
def get_password_hash(password: str):
    return password_hash.hash(password)

# will be used later when they try to log in. 
# It compares a typed password against the hashed in the database to see if they match
def verify_password(plain_password: str, hashed_password: str) :
    return password_hash.verify(plain_password, hashed_password)

# the json bodey the user sends when they sign up
class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(min_length=5, max_length=20)
    avatar_url: str = Field(default="")
    password: str = Field(min_length=8, max_length=20)

# what we send back to the client
class User(BaseModel):
    model_config = ConfigDict(from_attributes=True) # it tells pydantic to read data directly from my SQLAlchemy database objects
    id: int
    email: EmailStr
    name: str
    avatar_url: Optional[str] = None

# combines User model with jwt into one json response
class TokenResponse(BaseModel):
    user: User
    access_token: str
    token_type: str = "bearer"


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

@router.post("/login")
def login():
    pass

@router.post("/signup")
def signup(user_create: UserCreate, db = Depends(get_db)):
    existing_user = db.query(UserRecord).filter(UserRecord.email == str(user_create.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email is already registered."
        )
    hash_password = get_password_hash(user_create.password)
    # hash_password = hashlib.sha256(user_create.password.encode()).hexdigest()

    # it maps the data into a UserRecord
    new_user = UserRecord(
        email = str(user_create.email),
        name = user_create.name,
        avatar_url = user_create.avatar_url or None,
        password_hash = hash_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # converts the database row back into a safe Pydantic model
    user = User.model_validate(new_user)
 
    # it packages the User's id to create_access_token
    token_data = {"sub": str(user.id)}
    access_token = create_access_token(data=token_data)
    return TokenResponse(user = user, access_token = access_token)