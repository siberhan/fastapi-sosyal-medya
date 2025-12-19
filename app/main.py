from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# --- DÜZELTİLEN KISIMLAR (Relative Imports) ---
from . import models               # 'import models' yerine
from .database import engine       # 'from app.database' yerine (aynı klasördeyiz)
from .routers import post, user, auth, vote # 'from routers' yerine
# ----------------------------------------------

from fastapi_limiter import FastAPILimiter
from redis import asyncio as aioredis
import os

# Tabloları oluştur (Alembic kullanıyorsan burası opsiyoneldir ama kalsın)
#models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- 2. DEĞİŞİKLİK: GÜVENLİK ZIRHI (YENİ EKLENEN KISIM) ---
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    # Tarayıcıya: "Dosya türünü tahmin etmeye çalışma"
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Tarayıcıya: "Bu siteyi iframe içine alıp sahte buton koyamazsın"
    response.headers["X-Frame-Options"] = "DENY"
    return response
# ----------------------------------------------------------

@app.on_event("startup")
async def startup():
    # Docker içindeki servis adı "redis". Lokal testte "localhost"
    redis_host = os.environ.get("REDIS_HOSTNAME", "localhost")
    try:
        redis = aioredis.from_url(f"redis://{redis_host}", encoding="utf-8", decode_responses=True)
        await FastAPILimiter.init(redis)
        print("✅ Redis bağlantısı ve Rate Limiter başarıyla başlatıldı.")
    except Exception as e:
        print(f"⚠️ Redis bağlantı hatası: {e}")
        print("Rate Limiting devre dışı kalabilir.")
# ---------------------------------

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