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
from unittest.mock import MagicMock, AsyncMock
from fastapi_limiter import FastAPILimiter
# --------------------------------------

# 1. VERİTABANI BAĞLANTISI
SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}_test"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- SİHİRLİ FIXTURE (Redis ve Identifier Mock) ---
@pytest.fixture(autouse=True)
def mock_redis_for_limiter():
    """
    Bu fixture her testten önce otomatik çalışır.
    FastAPILimiter'ın redis bağlantısını VE tanımlayıcısını taklit eder.
    """
    # 1. Redis'i Mockla (AsyncMock ile)
    mock_redis = AsyncMock()
    mock_redis.pipeline.return_value.__aenter__.return_value = AsyncMock()
    FastAPILimiter.redis = mock_redis
    
    # 2. Identifier'ı Mockla (HATA BURADAYDI! EKLENDİ ✅)
    # Kütüphane "Bu kim?" diye sorduğunda "127.0.0.1" cevabını verecek sahte fonksiyon.
    async def mock_identifier(request):
        return "127.0.0.1"
    
    FastAPILimiter.identifier = mock_identifier
    
    yield
    
    # Temizlik
    FastAPILimiter.redis = None
    FastAPILimiter.identifier = None
# ------------------------------------

# 2. SESSION FIXTURE
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

# 3. STANDART CLIENT
@pytest.fixture()
def client(session):
    def override_get_db():
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

# 4. TEST USER
@pytest.fixture
def test_user(client):
    user_data = {"email": "testuser@gmail.com", "password": "password123"}
    res = client.post("/users/", json=user_data)
    assert res.status_code == 201
    new_user = res.json()
    new_user['password'] = user_data['password']
    return new_user

# 5. TOKEN
@pytest.fixture
def token(test_user):
    return create_access_token({"user_id": test_user['id']})

# 6. AUTHORIZED CLIENT
@pytest.fixture
def authorized_client(client, token):
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {token}"
    }
    return client

# 7. TEST POSTS
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