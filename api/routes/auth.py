
from fastapi import APIRouter
from fastapi import Depends
from db.database import get_db
from db.models import UserRecord

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
def login():
    pass

@router.post("/signup")
def signup(db = Depends(get_db)):
    new_user = UserRecord(
        email = "test@.test.com",
        name = "User Test",
        avatar_url = "avatar.png",
        password_hash = "hashed_passw"
    )
    
    db.add(new_user)
    db.commit()

    return { "user" : new_user}