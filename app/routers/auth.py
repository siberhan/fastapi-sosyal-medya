from fastapi import APIRouter, Depends, status, HTTPException, Response
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .. import database, schemas, models, utils, oauth2
from fastapi_limiter.depends import RateLimiter 

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