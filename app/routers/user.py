from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from typing import List

# --- DÜZELTİLEN KISIMLAR (Relative Imports) ---
# app.schemas, app.utils yerine ..schemas, ..utils kullanıyoruz
from .. import models, schemas, utils
from ..database import get_db
from .. import oauth2  # Login kontrolü için
# ----------------------------------------------

router = APIRouter(
    prefix="/users",
    tags=['Users']
)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Hash işlemi
    hashed_password = utils.hash(user.password)
    user.password = hashed_password
    
    new_user = models.User(**user.dict())
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        # Aynı email hatası için basit önlem (Daha detaylısı ileride)
        print(e) # Hatayı terminalde görmek için
        raise HTTPException(status_code=400, detail="Error creating user (Email already exists?)")
    return new_user

@router.get("/{id}", response_model=schemas.UserOut)
def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"User with id: {id} does not exist")
    return user

# 1. GET ALL
@router.get("/", response_model=List[schemas.UserOut])
def get_users(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    return users

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(id: int, 
                db: Session = Depends(get_db), 
                current_user: int = Depends(oauth2.get_current_user)):
    
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Buna yetkiniz yok")

    delete_query = db.query(models.User).filter(models.User.id == id)
    if delete_query.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail = f"user with {id} does not exist")
    delete_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{id}", status_code=status.HTTP_200_OK)
def update_user(id: int,
                updated_user: schemas.UserUpdate,
                db: Session = Depends(get_db),
                current_user: int = Depends(oauth2.get_current_user)):
    update_query = db.query(models.User).filter(models.User.id == id)
    user = update_query.first()
    if user.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Buna yetkiniz yok")
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"user with {id} does not exist")
    if updated_user.password:
        hashed_password = utils.hash(updated_user.password)
        updated_user.password = hashed_password

    update_query.update(updated_user.dict(exclude_unset=True), synchronize_session=False)

    db.commit()

    return update_query.first() # Güncel halini döndür