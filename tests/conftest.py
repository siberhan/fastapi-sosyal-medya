from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.config import settings
from app.database import get_db, Base
from app.oauth2 import create_access_token
from app import models
import pytest

# --- MOCKING İÇİN GEREKLİ IMPORTLAR ---
from unittest.mock import MagicMock, AsyncMock # AsyncMock eklendi!
from fastapi_limiter import FastAPILimiter
# --------------------------------------

# 1. VERİTABANI BAĞLANTISI
SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}_test"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- SİHİRLİ FIXTURE (Redis Mock) ---
@pytest.fixture(autouse=True)
def mock_redis_for_limiter():
    """
    Bu fixture her testten önce otomatik çalışır.
    FastAPILimiter'ın redis bağlantısını AsyncMock ile taklit eder.
    Böylece 'await redis...' çağrıları testte hata vermez.
    """
    # AsyncMock kullanıyoruz çünkü kütüphane 'await' kullanıyor
    mock_redis = AsyncMock()
    # Pipeline çağrıları da zincirleme çalıştığı için onları da mockluyoruz
    mock_redis.pipeline.return_value.__aenter__.return_value = AsyncMock() 
    
    FastAPILimiter.redis = mock_redis
    yield
    FastAPILimiter.redis = None
# ------------------------------------

# 2. SESSION FIXTURE (DB TABLOLARINI YÖNETİR)
@pytest.fixture()
def session():
    print("Test veritabanı tabloları oluşturuluyor...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# 3. STANDART CLIENT (GİRİŞ YAPMAMIŞ)
@pytest.fixture()
def client(session):
    # Dependency override ile RateLimiter'ı ezmeye GEREK YOK.
    # Çünkü yukarıda Redis'i mockladık, Limiter çalışacak ama Redis var sanacak.

    def override_get_db():
        try:
            yield session
        finally:
            session.close()

    # DÜZELTME: Bu satır kesinlikle fonksiyonun DIŞINDA olmalı (Girinti Hatası Giderildi)
    app.dependency_overrides[get_db] = override_get_db
    
    yield TestClient(app)
    
    # Temizlik
    app.dependency_overrides.clear()

# 4. TEST USER FIXTURE (OTOMATİK KULLANICI OLUŞTURUR)
@pytest.fixture
def test_user(client):
    user_data = {"email": "testuser@gmail.com", "password": "password123"}
    res = client.post("/users/", json=user_data)
    assert res.status_code == 201
    new_user = res.json()
    new_user['password'] = user_data['password']
    return new_user

# 5. TOKEN FIXTURE (KULLANICI İÇİN TOKEN ÜRETİR)
@pytest.fixture
def token(test_user):
    return create_access_token({"user_id": test_user['id']})

# 6. AUTHORIZED CLIENT (TOKEN EKLENMİŞ İSTEMCİ)
@pytest.fixture
def authorized_client(client, token):
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {token}"
    }
    return client

# 7. TEST POSTS FIXTURE (DB'YE HAZIR POSTLAR EKLER)
@pytest.fixture
def test_posts(test_user, session):
    posts_data = [{
        "title": "1. Post Başlığı",
        "content": "1. İçerik",
        "owner_id": test_user['id']
    }, {
        "title": "2. Post Başlığı",
        "content": "2. İçerik",
        "owner_id": test_user['id']
    }, {
        "title": "3. Post Başlığı",
        "content": "3. İçerik",
        "owner_id": test_user['id']
    }]
    
    # Map fonksiyonu ile sözlükleri Post modeline çeviriyoruz
    def create_post_model(post):
        return models.Post(**post)
    
    post_map = map(create_post_model, posts_data)
    posts = list(post_map)
    
    session.add_all(posts)
    session.commit()
    
    posts = session.query(models.Post).all()
    return posts

@pytest.fixture
def test_vote(test_posts, session, test_user):
    new_vote = models.Vote(post_id=test_posts[0].id, user_id=test_user['id'])
    session.add(new_vote)
    session.commit()