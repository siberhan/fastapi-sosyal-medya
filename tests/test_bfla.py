import pytest
from app import models

def test_delete_user_as_admin_success(authorized_client, test_user, session):
    """
    1. SENARYO: Admin yetkisi olan biri kullanıcı silebilir mi? (BFLA CHECK)
    """
    # 1. Şu anki kullanıcımızı (authorized_client) veritabanında 'admin' yapalım.
    # Normalde veritabanında 'user' olarak kayıtlı.
    user = session.query(models.User).filter(models.User.id == test_user['id']).first()
    user.role = "admin"
    session.commit()
    
    # 2. Silinecek Rastgele Bir Kullanıcı Oluştur (Kurban)
    res = authorized_client.post("/users/", json={"email": "silinecek@gmail.com", "password": "123"})
    kurban_id = res.json()['id']
    
    # 3. Admin yetkisiyle silme isteği at
    res = authorized_client.delete(f"/users/{kurban_id}")
    
    # Beklenen: 204 No Content (Başarılı)
    assert res.status_code == 204

def test_delete_user_as_normal_user_fail(client, test_user, session):
    """
    2. SENARYO: Normal bir kullanıcı (Hacker), admin endpointini denerse?
    """
    # 1. Normal bir kullanıcı oluştur ve giriş yap
    res = client.post("/users/", json={"email": "normal@gmail.com", "password": "123"})
    normal_user = res.json()
    
    login_res = client.post("/login", data={"username": "normal@gmail.com", "password": "123"})
    token = login_res.json()['access_token']
    
    client.headers = {**client.headers, "Authorization": f"Bearer {token}"}
    
    # 2. Admin olmadığı halde silme isteği atıyor!
    # Kimi sildiğinin önemi yok, sistemin reddetmesi lazım.
    res = client.delete(f"/users/{test_user['id']}")
    
    # Beklenen: 403 Forbidden (YASAK!)
    assert res.status_code == 403