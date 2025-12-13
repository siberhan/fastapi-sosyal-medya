from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
import schemas, database, models, oauth2

router = APIRouter(
    prefix="/vote",
    tags=['Vote']
)

@router.post("/", status_code=status.HTTP_201_CREATED)
def vote(vote: schemas.Vote, db: Session = Depends(database.get_db), current_user: int = Depends(oauth2.get_current_user)):

    # 1. Önce böyle bir Post var mı diye kontrol et
    # (Olmayan bir postu beğenemezsin)
    post = db.query(models.Post).filter(models.Post.id == vote.post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id: {vote.post_id} does not exist")

    # 2. Bu kullanıcı bu post için daha önce oy kullanmış mı?
    vote_query = db.query(models.Vote).filter(
        models.Vote.post_id == vote.post_id, 
        models.Vote.user_id == current_user.id
    )
    found_vote = vote_query.first()

    # --- SENARYO A: BEĞENMEK İSTİYOR (dir = 1) ---
    if (vote.dir == 1):
        if found_vote:
            # Zaten beğenmişse hata ver
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"User {current_user.id} has already voted on post {vote.post_id}")
        
        # Beğenmemişse yeni oy oluştur
        new_vote = models.Vote(post_id=vote.post_id, user_id=current_user.id)
        db.add(new_vote)
        db.commit()
        return {"message": "successfully added vote"}

    # --- SENARYO B: BEĞENİYİ GERİ ALMAK İSTİYOR (dir = 0) ---
    else:
        if not found_vote:
            # Zaten beğenmemiş ki, neyi geri alacak?
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vote does not exist")
        
        # Beğenmişse oyu sil
        vote_query.delete(synchronize_session=False)
        db.commit()
        return {"message": "successfully deleted vote"}