import pytest
from app import models

def test_delete_other_user_post(client, test_user, test_posts):
    """
    BOLA TESTİ:
    Senaryo: Hacker kullanıcısı, test_user'a ait bir postu silmeye çalışıyor.
    Beklenen: 403 Forbidden
    """
    
    # 1. Hacker Kullanıcısını Oluştur
    res = client.post("/users/", json={"email": "hacker@gmail.com", "password": "password123"})
    assert res.status_code == 201
    
    # 2. Hacker Olarak Giriş Yap (Token Al)
    res_login = client.post("/login", data={"username": "hacker@gmail.com", "password": "password123"})
    token = res_login.json()['access_token']
    
    # 3. Hacker'ın Yetkili İstemcisini Hazırla
    # Standart client'ın header'ını hacker'ın token'ı ile güncelliyoruz
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {token}"
    }
    
    # 4. Hedef: test_user'a ait olan ilk post (Fixture'dan geliyor)
    target_post_id = test_posts[0].id
    
    # 5. SALDIRI ANI: DELETE isteği at
    res = client.delete(f"/posts/{target_post_id}")
    
    # 6. SONUÇ KONTROLÜ
    # Eğer kodun güvenliyse 403 dönmeli.
    # Eğer BOLA açığın varsa 204 döner ve bu assertion hata verir.
    assert res.status_code == 403