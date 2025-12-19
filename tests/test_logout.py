import pytest
from app import schemas

def test_logout_invalidates_token(client, test_user):
    res_login = client.post("/login", data={"username": test_user['email'], "password": test_user['password']})
    token = res_login.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    res = client.get("/posts/", headers=headers)
    assert res.status_code == 200

    res_logout = client.post("/logout", headers=headers)
    assert res_logout.status_code == 200

    res_after_logout = client.get("/posts/", headers=headers)
    assert res_after_logout.status_code == 401
    