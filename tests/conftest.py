from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.config import settings
from app.database import get_db, Base
from app.oauth2 import create_access_token, get_current_user # <--- get_current_user eklendi
from app import models
import pytest

# Auth dosyasındaki Rate Limiter'ı bypass etmek için çağırıyoruz
from app.routers.auth import login_limiter

# 1. VERİTABANI BAĞLANTISI
# Pipeline dosyasındaki (fastapi_test) ile birebir uyumlu hale getirildi (sondaki ek silindi)
SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. SESSION FIXTURE
@pytest.fixture()
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# 3. STANDART CLIENT (Bypass işlemleri burada yapılır)
@pytest.fixture()
def client(session):
    
    # --- OVERRIDE 1: Veritabanı ---
    def override_get_db():
        try:
            yield session
        finally:
            pass

    # --- OVERRIDE 2: Rate Limiter (Redis'e gitmesin) ---
    app.dependency_overrides[login_limiter] = lambda: None

    # --- OVERRIDE 3: OAuth2 Redis Kontrolü (401 hatasını çözen kısım!) ---
    # Testler sırasında Redis kara liste kontrolünü atlayıp direkt kullanıcıyı dönüyoruz
    async def override_get_current_user():
        user = session.query(models.User).filter(models.User.email == "testuser@gmail.com").first()
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    yield TestClient(app)
    
    # Test bittikten sonra ayarları temizle
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
    posts_data = [
        {"title": "1. Post Başlığı", "content": "1. İçerik", "owner_id": test_user['id']},
        {"title": "2. Post Başlığı", "content": "2. İçerik", "owner_id": test_user['id']},
        {"title": "3. Post Başlığı", "content": "3. İçerik", "owner_id": test_user['id']}
    ]
    posts = [models.Post(**post) for post in posts_data]
    session.add_all(posts)
    session.commit()
    return session.query(models.Post).all()