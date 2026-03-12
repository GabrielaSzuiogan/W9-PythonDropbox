from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from .config import settings 

password_hash = PasswordHash((Argon2Hasher(),))

# takes the password a user types and turns it into a long, scrambled string
def get_password_hash(password: str):
    return password_hash.hash(password)

# will be used later when they try to log in. 
# It compares a typed password against the hashed in the database to see if they match
def verify_password(plain_password: str, hashed_password: str):
    return password_hash.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt