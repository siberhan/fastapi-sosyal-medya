from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import database, schemas, models, utils, oauth2
from fastapi_limiter.depends import RateLimiter 
from redis import asyncio as aioredis
from ..config import settings
# Gerekli ek importlar (Eğer yukarıda yoksa ekle)
from jose import JWTError, jwt
from ..oauth2 import SECRET_KEY, ALGORITHM

router = APIRouter(tags=['Authentication'])

# Rate Limiter: 60 saniyede en fazla 5 giriş denemesi
login_limiter = RateLimiter(times=5, seconds=60)

# Redis bağlantı adresi (Config'den çekiliyor)
REDIS_URL = f"redis://{settings.redis_hostname}:{settings.redis_port}"

# --- LOGIN ENDPOINT (ÇİFT TOKEN ÜRETİR) ---
@router.post('/login', response_model=schemas.Token, dependencies=[Depends(login_limiter)])
async def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):

    # 1. Kullanıcıyı bul
    user = db.query(models.User).filter(models.User.email == user_credentials.username).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")

    # 2. Şifreyi doğrula
    if not utils.verify(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")

    # 3. Access Token Üret (Kısa Süreli)
    access_token = oauth2.create_access_token(data={"user_id": user.id})

    # 4. Refresh Token Üret (Uzun Süreli)
    refresh_token = oauth2.create_refresh_token(data={"user_id": user.id})

    # 5. Refresh Token'ı Redis'e Kaydet (TTL ile)
    redis = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    
    # Anahtar: refresh_token:1 (User ID)
    # TTL: 7 gün (Saniye cinsinden)
    await redis.set(
        f"refresh_token:{user.id}", 
        refresh_token, 
        ex=settings.refresh_token_expire_days * 24 * 60 * 60
    )
    await redis.close()

    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer"
    }

# --- LOGOUT ENDPOINT (HER ŞEYİ TEMİZLER) ---
@router.post('/logout', status_code=status.HTTP_200_OK)
async def logout(token: str = Depends(oauth2.oauth2_scheme), 
                 current_user: models.User = Depends(oauth2.get_current_user)):
    
    redis = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    
    # 1. Mevcut Access Token'ı Kara Listeye Al (Süresi dolana kadar)
    await redis.set(f"blacklist:{token}", "true", ex=settings.access_token_expire_minutes * 60) 
    
    # 2. Redis'teki Refresh Token'ı Sil (Artık yeni access token alamasın)
    await redis.delete(f"refresh_token:{current_user.id}")
    
    await redis.close()
    
    return {"message": "Başarıyla çıkış yapıldı. Oturum tamamen sonlandırıldı."}




# --- REFRESH TOKEN İLE YENİ TOKEN ALMA ---
@router.post('/refresh', response_model=schemas.Token)
async def refresh_token(refresh_token: str, db: Session = Depends(database.get_db)):
    
    redis = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    
    try:
        # 1. Gelen Refresh Token'ın imzasını kontrol et
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz Refresh Token")
            
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh Token süresi dolmuş veya hatalı")

    # 2. Redis'te bu kullanıcıya ait kayıtlı token duruyor mu?
    # Hatırla: Logout olunca bunu siliyorduk.
    stored_token = await redis.get(f"refresh_token:{user_id}")

    # 3. Gelen token ile Redis'teki token eşleşiyor mu?
    # Bu adım çalınmış token'ların tekrar kullanılmasını engeller (Reuse Detection)
    if not stored_token or stored_token != refresh_token:
        # Eğer eşleşmiyorsa bu şüpheli bir durumdur, her ihtimale karşı Redis'teki kaydı sil
        await redis.delete(f"refresh_token:{user_id}")
        await redis.close()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Oturum geçersiz, lütfen tekrar giriş yapın.")

    # 4. HER ŞEY OK! Yeni bir ikili (Access + Refresh) üret (ROTATION)
    new_access_token = oauth2.create_access_token(data={"user_id": user_id})
    new_refresh_token = oauth2.create_refresh_token(data={"user_id": user_id})

    # 5. Yeni Refresh Token'ı Redis'e yaz (Eskisinin üzerine yazar)
    await redis.set(
        f"refresh_token:{user_id}", 
        new_refresh_token, 
        ex=settings.refresh_token_expire_days * 24 * 60 * 60
    )
    await redis.close()

    return {
        "access_token": new_access_token, 
        "refresh_token": new_refresh_token, 
        "token_type": "bearer"
    }