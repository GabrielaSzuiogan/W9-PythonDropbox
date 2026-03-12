from fastapi import APIRouter, Depends, HTTPException, status
from db.database import get_db
from db.models import UserRecord
from utils import get_password_hash, create_access_token
from api.schemas import UserCreate, User, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
def login():
    pass

@router.post("/signup", response_model=TokenResponse)
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
 
    # it packages the User's id into token
    token_data = {"sub": str(user.id)}
    access_token = create_access_token(data = token_data)

    return TokenResponse(user = user, access_token = access_token)