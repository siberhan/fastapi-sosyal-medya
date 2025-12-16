from app import schemas
import pytest

# 1. TÜM POSTLARI ÇEKME TESTİ
def test_get_all_posts(authorized_client, test_posts):
    res = authorized_client.get("/posts/")
    
    # Doğrulama: Gelen veri bir liste mi? Uzunluğu bizim eklediğimiz kadar mı?
    # test_posts fixture'ı 3 tane post eklemişti.
    assert len(res.json()) == len(test_posts)
    assert res.status_code == 200

# 2. TEK POST ÇEKME TESTİ
def test_get_one_post(authorized_client, test_posts):
    res = authorized_client.get(f"/posts/{test_posts[0].id}")
    post = schemas.PostOut(**res.json())
    
    assert post.Post.id == test_posts[0].id
    assert post.Post.content == test_posts[0].content

# 3. YENİ POST OLUŞTURMA TESTİ
@pytest.mark.parametrize("title, content, published", [
    ("Yeni Başlık 1", "Yeni İçerik 1", True),
    ("Pizzayı Severim", "Pepperoni olsun", False),
    ("En sevdiğim renk", "Mavi", True),
])
def test_create_post(authorized_client, test_user, title, content, published):
    res = authorized_client.post("/posts/", json={"title": title, "content": content, "published": published})
    
    created_post = schemas.Post(**res.json())
    
    assert res.status_code == 201
    assert created_post.title == title
    assert created_post.owner_id == test_user['id']

# 4. GİRİŞ YAPMADAN POST SİLME (UNAUTHORIZED)
def test_delete_post_unauthorized(client, test_user, test_posts):
    res = client.delete(f"/posts/{test_posts[0].id}")
    assert res.status_code == 401

# 5. BAŞARILI SİLME İŞLEMİ
def test_delete_post_success(authorized_client, test_user, test_posts):
    res = authorized_client.delete(f"/posts/{test_posts[0].id}")
    assert res.status_code == 204