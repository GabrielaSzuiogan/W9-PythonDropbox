from fastapi import APIRouter


router = APIRouter(tags=["core"])

@router.get("/")
def root():
    return {"message": "Chatbox API is running ok!"}

@router.get("/health")
def health():
    return {"status" : "ok"}


