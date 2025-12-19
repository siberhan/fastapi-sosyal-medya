from fastapi import APIRouter, Depends, status, HTTPException, Response
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import database, schemas, models, utils, oauth2
from fastapi_limiter.depends import RateLimiter 
from redis import asyncio as aioredis
import os


router = APIRouter(tags=['Authentication'])

# 1. KURALI BİR DEĞİŞKENE ATIYORUZ (İsimlendiriyoruz)
# Böylece test dosyasından bu ismi çağırıp "Bunu iptal et" diyebileceğiz.
login_limiter = RateLimiter(times=5, seconds=60)

@router.post('/login', response_model=schemas.Token,
             # 2. ARTIK İSMİYLE ÇAĞIRIYORUZ
             dependencies=[Depends(login_limiter)]) 
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):

    user = db.query(models.User).filter(models.User.email == user_credentials.username).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")

    if not utils.verify(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")

    access_token = oauth2.create_access_token(data={"user_id": user.id})

    return {"access_token": access_token, "token_type": "bearer"}   

# app/routers/auth.py
from redis import asyncio as aioredis
import os

@router.post('/logout', status_code=status.HTTP_200_OK)
async def logout(token: str = Depends(oauth2.oauth2_scheme), 
                 current_user: models.User = Depends(oauth2.get_current_user)):
    
    # 1. Redis'e bağlan
    redis = aioredis.from_url(f"redis://{os.environ.get('REDIS_HOSTNAME', 'localhost')}", 
                              encoding="utf-8", decode_responses=True)
    
    # 2. Token'ı kara listeye ekle
    # 'ex=1800' (30 dakika) - Token zaten 30 dk sonra kendiliğinden ölecek. 
    # Redis'te sonsuza kadar tutmaya gerek yok.
    await redis.set(f"blacklist:{token}", "true", ex=1800) 
    
    await redis.close()
    
    return {"message": "Başarıyla çıkış yapıldı. Token imha edildi."}