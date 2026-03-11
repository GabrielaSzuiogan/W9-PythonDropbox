
from fastapi import APIRouter


router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
def login():
    pass

@router.post("/signup")
def signup():
    pass