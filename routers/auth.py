from fastapi import APIRouter, Depends, status, HTTPException, Response
from sqlalchemy.orm import Session
import database, schemas, models, utils, oauth2 # Gerekli dosyaları çağırıyoruz

router = APIRouter(tags=['Authentication'])

@router.post('/login', response_model=schemas.Token)
def login(user_credentials: schemas.UserLogin, db: Session = Depends(database.get_db)):
    
    # 1. Email'e göre kullanıcıyı bul
    user = db.query(models.User).filter(models.User.email == user_credentials.email).first()

    # 2. Kullanıcı yoksa hata ver
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")

    # 3. Şifreyi doğrula (Hash kontrolü)
    if not utils.verify(user_credentials.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid Credentials")
    access_token = oauth2.create_access_token(data={"user_id": user.id})
    # 4. Token Oluştur (Şimdilik sahte token dönüyoruz, bir sonraki adımda JWT yapacağız)
    return {"access_token": access_token, "token_type": "bearer"}