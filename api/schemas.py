from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# the json bodey the user sends when they sign up
class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(min_length=5, max_length=20)
    avatar_url: str = Field(default="")
    password: str = Field(min_length=8, max_length=20)

# what we send back to the client
class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    name: str
    avatar_url: Optional[str] = None

# combines User model with jwt into one json response
class TokenResponse(BaseModel):
    user: User
    access_token: str
    token_type: str = "bearer"