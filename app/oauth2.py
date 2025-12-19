from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .config import settings
from . import schemas, database, models
import os
from redis import asyncio as aioredis
import uuid

# --- AUTH CONFIGURATION ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.refresh_token_expire_days
REDIS_URL = f"redis://{os.environ.get('REDIS_HOSTNAME', 'localhost')}"

def create_access_token(data: dict):
    """
    Kısa süreli Access Token üretir.
    'jti' (JWT ID) eklenerek testlerdeki çakışmalar önlenmiştir.
    """
    to_encode = data.copy()
    to_encode.update({"jti": str(uuid.uuid4())})
    
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    """
    Uzun süreli Refresh Token üretir.
    Hırsızlık tespiti için eşsiz jti içerir.
    """
    to_encode = data.copy()
    to_encode.update({"jti": str(uuid.uuid4())})
    
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_access_token(token: str, credentials_exception):
    """Token geçerliliğini doğrular."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        
        if user_id is None:
            raise credentials_exception
        token_data = schemas.TokenData(id=str(user_id))
    except JWTError:
        raise credentials_exception
        
    return token_data

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    """
    Kullanıcı kimlik doğrulama ve Redis kara liste kontrolü.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Redis bağlantısı ve kara liste kontrolü
    redis = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    try:
        is_blacklisted = await redis.get(f"blacklist:{token}")
        if is_blacklisted:
            raise credentials_exception
    finally:
        await redis.close()

    # Token ve veritabanı doğrulama
    token_data = verify_access_token(token, credentials_exception)
    user = db.query(models.User).filter(models.User.id == token_data.id).first()
    
    if user is None:
        raise credentials_exception
        
    return user