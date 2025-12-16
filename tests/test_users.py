from app import schemas
from app.config import settings
from jose import jwt
import pytest

# 1. KULLANICI OLUŞTURMA TESTİ
def test_create_user(client):
    email = "testdeneme@gmail.com" # nosec B105
    password = "password123" # nosec B105
    
    res = client.post("/users/", json={"email": email, "password": password})
    
    # Oluşturulan kullanıcıyı şemaya göre doğrula
    new_user = schemas.UserOut(**res.json())
    
    assert res.status_code == 201
    assert new_user.email == email


# 2. GİRİŞ YAPMA (LOGIN) TESTİ
def test_login_user(client):
    # Önce bir kullanıcı oluşturuyoruz (client fixture'ı temiz DB verdiği için)
    email = "giris@gmail.com" # nosec B105
    password = "123" # nosec B105
    client.post("/users/", json={"email": email, "password": password})
    
    # Şimdi giriş yapmayı deniyoruz (Form Data olarak gider)
    res = client.post("/login", data={"username": email, "password": password})
    
    # Token şemasına uyuyor mu?
    login_res = schemas.Token(**res.json())
    
    # Token'ı decode edip içindeki ID'yi kontrol edelim
    payload = jwt.decode(login_res.access_token, settings.secret_key, algorithms=[settings.algorithm])
    id = payload.get("user_id")
    
    assert id is not None
    assert login_res.token_type == "bearer" # nosec B105
    assert res.status_code == 200

# 3. HATALI GİRİŞ TESTLERİ (PARAMETRİZE)
# Tek fonksiyonda 3 farklı senaryoyu deniyoruz
@pytest.mark.parametrize("email, password, status_code", [
    ('yanlisemail@gmail.com', '123', 403),   # Yanlış Email
    ('giris@gmail.com', 'yanlissifre', 403), # Yanlış Şifre
    ('yanlisemail@gmail.com', 'yanlissifre', 403), # İkisi de yanlış
    (None, '123', 422), # Email yok (Validation hatası)
    ('giris@gmail.com', None, 422) # Şifre yok (Validation hatası)
])
def test_incorrect_login(client, email, password, status_code):
    # Doğru kullanıcıyı oluştur
    client.post("/users/", json={"email": "giris@gmail.com", "password": "123"})
    
    # Yanlış verilerle giriş dene
    res = client.post("/login", data={"username": email, "password": password})
    
    assert res.status_code == status_code