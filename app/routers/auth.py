from fastapi import APIRouter, Depends, status, HTTPException, Response
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from fastapi_limiter.depends import RateLimiter

# --- DÜZELTİLEN KISIM (Relative Imports) ---
# app.database, models vb. yerine ..database, ..models kullanıyoruz
from .. import database, schemas, models, utils, oauth2
# ----------------------------------------------

router = APIRouter(tags=['Authentication'])

@router.post('/login', response_model=schemas.Token,
             dependencies=[Depends(RateLimiter(times=5, seconds=60))])
def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):

    # Kullanıcıyı email ile bul
    # OAuth2PasswordRequestForm kullandığımız için email verisi 'username' alanında tutulur
    user = db.query(models.User).filter(models.User.email == user_credentials.username).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")

    # Şifreyi doğrula
    if not utils.verify(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")

    # Token oluştur
    access_token = oauth2.create_access_token(data={"user_id": user.id})

    return {"access_token": access_token, "token_type": "bearer"}


