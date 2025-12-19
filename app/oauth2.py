from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .config import settings
from . import schemas, database, models
import os
from redis import asyncio as aioredis # <--- Redis için eklendi
import uuid

# Login URL'si
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.refresh_token_expire_days
# Redis bağlantı adresi
REDIS_URL = f"redis://{os.environ.get('REDIS_HOSTNAME', 'localhost')}"

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- YENİ: Refresh Token üreten fonksiyon ---
def create_refresh_token(data: dict):
    to_encode = data.copy()
    
    # Her refresh token'a benzersiz bir "jti" (JWT ID) veriyoruz
    # Bu, ileride Redis'te kontrol yaparken çok işimize yarayacak
    to_encode.update({"jti": str(uuid.uuid4())})
    
    # Süresini gün bazında ayarlıyoruz (örn: 7 gün)
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: str = payload.get("user_id")
        if id is None:
            raise credentials_exception
        token_data = schemas.TokenData(id=str(id))
    except JWTError:
        raise credentials_exception
    return token_data

# --- GÜNCELLENEN KRİTİK FONKSİYON ---
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. ADIM: KARA LİSTE KONTROLÜ
    # Redis'e bağlanıp bu token yasaklı mı bakıyoruz
    redis = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    is_blacklisted = await redis.get(f"blacklist:{token}")
    await redis.close()

    if is_blacklisted:
        # Eğer Redis'te bu token varsa, süresi geçmemiş olsa bile kovuyoruz!
        raise credentials_exception

    # 2. ADIM: TOKEN DOĞRULAMA (Eski mantık)
    token_data = verify_access_token(token, credentials_exception)
    
    # 3. ADIM: VERİTABANI KONTROLÜ
    user = db.query(models.User).filter(models.User.id == token_data.id).first()
    
    if user is None:
        raise credentials_exception
        
    return user