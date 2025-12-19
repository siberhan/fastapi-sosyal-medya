from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.config import settings
from app.database import get_db, Base
from app.oauth2 import create_access_token
from app import models
import pytest
from app.routers.auth import login_limiter

# 1. VERİTABANI BAĞLANTISI (Tek Test İsimlendirmesi)
SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.database_username}:{settings.database_password}@{settings.database_hostname}:{settings.database_port}/{settings.database_name}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture()
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture()
def client(session):
    def override_get_db():
        try:
            yield session
        finally:
            pass
    
    # Sadece Limiter'ı bypass ediyoruz, auth'a dokunmuyoruz ki güvenlik testleri çalışsın
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[login_limiter] = lambda: None
    
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(client):
    user_data = {"email": "testuser@gmail.com", "password": "password123"}
    res = client.post("/users/", json=user_data)
    assert res.status_code == 201
    new_user = res.json()
    new_user['password'] = user_data['password']
    return new_user

@pytest.fixture
def token(test_user):
    return create_access_token({"user_id": test_user['id']})

@pytest.fixture
def authorized_client(client, token):
    client.headers = {**client.headers, "Authorization": f"Bearer {token}"}
    return client

@pytest.fixture
def test_posts(test_user, session):
    posts_data = [
        {"title": "1. Post", "content": "İçerik 1", "owner_id": test_user['id']},
        {"title": "2. Post", "content": "İçerik 2", "owner_id": test_user['id']},
    ]
    posts = [models.Post(**p) for p in posts_data]
    session.add_all(posts)
    session.commit()
    return session.query(models.Post).all()

# --- EKSİK OLAN FIXTURE BURADA! ---
@pytest.fixture
def test_vote(test_posts, session, test_user):
    new_vote = models.Vote(post_id=test_posts[0].id, user_id=test_user['id'])
    session.add(new_vote)
    session.commit()
    return new_vote