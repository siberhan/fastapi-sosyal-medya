from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import schemas, database, models
from config import settings

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

def create_access_token(data: dict):
    # Verinin kopyasını al (Asıl veriyi bozmamak için)
    to_encode = data.copy()

    # Süre bitiş zamanını hesapla (Şu an + 30 dakika)
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Bitiş süresini veriye ekle
    to_encode.update({"exp": expire})

    # Token'ı oluştur (Encode)
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


# Login URL'mizin '/login' olduğunu belirtiyoruz
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='login')

def verify_access_token(token: str, credentials_exception):
    try:
        # 1. Token'ı çöz (Decode)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 2. İçinden ID bilgisini al
        id: str = payload.get("user_id")
        
        if id is None:
            raise credentials_exception
            
        # 3. Şemaya uygun mu diye bak
        token_data = schemas.TokenData(id=str(id))
        
    except JWTError:
        raise credentials_exception
    
    return token_data

# Bizim asıl kullanacağımız fonksiyon bu:
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Token'ı doğrula
    token_data = verify_access_token(token, credentials_exception)
    
    # Veritabanından o kullanıcıyı bul
    user = db.query(models.User).filter(models.User.id == token_data.id).first()
    
    return user