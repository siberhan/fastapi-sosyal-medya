import pytest
from app import models

# 1. BAŞARILI OY VERME (LIKE)
def test_vote_on_post(authorized_client, test_posts):
    res =authorized_client.post(
        "/vote/", json={"post_id": test_posts[0].id, "dir":1}
    )
    assert res.status_code == 201

# 2. AYNI POSTA İKİ KEZ OY VERME (CONFLICT)
# test_vote fixture'ı sayesinde bu post zaten beğenilmiş durumda.
def test_vote_twice_post(authorized_client, test_posts, test_vote):
    res = authorized_client.post(
        "/vote/", json={"post_id": test_posts[0].id, "dir": 1})
    assert res.status_code == 409

# 3. OYU GERİ ÇEKME (UNLIKE)
# test_vote fixture'ı sayesinde zaten beğenilmiş, şimdi siliyoruz.
def test_delete_vote(authorized_client, test_posts, test_vote):
    res = authorized_client.post(
        "/vote/", json={"post_id": test_posts[0].id, "dir": 0})
    assert res.status_code == 201

# 4. OLMAYAN OYU SİLMEYE ÇALIŞMA (404)
# Kimse oy vermedi ama silmeye çalışıyoruz (dir=0)
def test_delete_vote_non_exist(authorized_client, test_posts):
    res = authorized_client.post(
        "/vote/", json={"post_id": test_posts[0].id, "dir": 0})
    assert res.status_code == 404

# 5. OLMAYAN POSTA OY VERME (404)
def test_vote_post_non_exist(authorized_client, test_posts):
    res = authorized_client.post(
        "/vote/", json={"post_id": 88888, "dir": 1})
    assert res.status_code == 404

# 6. GİRİŞ YAPMADAN OY VERME (UNAUTHORIZED)
def test_vote_unauthorized(client, test_posts):
    res = client.post(
        "/vote/", json={"post_id": test_posts[0].id, "dir": 1})
    assert res.status_code == 401
