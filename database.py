from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import settings # Import etmeyi unutma

# ESKİSİ: SQLALCHEMY_DATABASE_URL = "postgresql://postgres:12345@localhost/fastapi"

# YENİSİ: F-String kullanarak değişkenleri yerleştiriyoruz
SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# --- EKLENEN KISIM ---
# Bu fonksiyonu main.py'den buraya taşıdık ki tüm routerlar erişebilsin
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()