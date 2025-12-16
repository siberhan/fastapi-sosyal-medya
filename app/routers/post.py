from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func

# --- DÜZELTİLMİŞ KISIMLAR ---
from .. import models, schemas, oauth2
from ..database import get_db
# -----------------------------

# Router Tanımlaması
router = APIRouter(
    prefix="/posts",
    tags=['Posts']
)

# 1. GET ALL (Aynı kaldı)
@router.get("/", response_model=List[schemas.PostOut])
def get_posts(db: Session = Depends(get_db),
              current_user: int = Depends(oauth2.get_current_user),
              limit: int = 10,
              skip: int = 0,
              search: Optional[str] = ""):
    
    # Vote (Beğeni) sayılarını da getiren Join sorgusu
    posts = db.query(models.Post, func.count(models.Vote.post_id).label("votes"))\
        .join(models.Vote, models.Vote.post_id == models.Post.id, isouter=True)\
        .group_by(models.Post.id)\
        .filter(models.Post.title.contains(search))\
        .limit(limit)\
        .offset(skip)\
        .all()
        
    return posts

# 2. CREATE (Aynı kaldı)
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.Post)
def create_posts(post: schemas.PostCreate,
                 db: Session = Depends(get_db),
                 current_user: int = Depends(oauth2.get_current_user)):
    print(current_user.email)
    new_post = models.Post(owner_id=current_user.id, **post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

# 3. GET ONE (TEK POST ÇEKME ROTASI - JOIN SORGUSUYLA GÜNCELLENDİ)
@router.get("/{id}", response_model=schemas.PostOut) # PostOut şeması bekleniyor
def get_post(id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    
    # JOIN SORGUSU EKLENDİ: Artık Vote sayısını da çekiyor.
    post = db.query(models.Post, func.count(models.Vote.post_id).label("votes"))\
        .join(models.Vote, models.Vote.post_id == models.Post.id, isouter=True)\
        .group_by(models.Post.id)\
        .filter(models.Post.id == id).first()
    
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} was not found")
    
    # PostOut şemasına uyması için JOIN sonucu dönülmeli (Post objesi + votes sayısı)
    return post 

# 4. DELETE (Aynı kaldı)
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, current_user: int = Depends(oauth2.get_current_user), db: Session = Depends(get_db)):
    # 1. Silinecek postu bul
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post = post_query.first()
    # 2. Post yoksa 404 ver
    if post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} does not exist")
    # 3. Postun sahibi değilse silmesine izin verme (403)
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to perform requested action")

    post_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# 5. UPDATE (Aynı kaldı)
@router.put("/{id}", response_model=schemas.Post)
def update_post(id: int, updated_post: schemas.PostCreate, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    post = post_query.first()
    
    if post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id: {id} does not exist")
    
    if post.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to perform requested action")
    
    post_query.update(updated_post.dict(), synchronize_session=False)
    db.commit()
    return post_query.first()