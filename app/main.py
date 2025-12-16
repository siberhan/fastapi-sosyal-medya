from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --- DÜZELTİLEN KISIMLAR (Relative Imports) ---
from . import models               # 'import models' yerine
from .database import engine       # 'from app.database' yerine (aynı klasördeyiz)
from .routers import post, user, auth, vote # 'from routers' yerine
# ----------------------------------------------

# Tabloları oluştur (Alembic kullanıyorsan burası opsiyoneldir ama kalsın)
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

# Routerları ana uygulamaya dahil et
app.include_router(post.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(vote.router)

@app.get("/")
def root():
    return {"message": "Selamun Aleykum, burasi artik otomatik guncelleniyor! 🚀"}