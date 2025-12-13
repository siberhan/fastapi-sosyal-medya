from fastapi import FastAPI
import models
from database import engine
from routers import post, user, auth, vote
from fastapi.middleware.cors import CORSMiddleware

# Tabloları oluştur
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,      # İzin verilen siteler
    allow_credentials=True,     # Çerezlere (Cookie) izin ver
    allow_methods=["*"],        # Tüm metodlara izin ver (GET, POST, DELETE...)
    allow_headers=["*"],        # Tüm başlıklara (Header) izin ver
)


# Routerları ana uygulamaya dahil et (Include)
app.include_router(post.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(vote.router)

@app.get("/")
def root():
    return {"message": "Hello World"}