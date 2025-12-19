import pytest

def test_login_sql_injection_attempt(client):
    malicious_email = "admin@gmail.com ' OR '1'='1"

    payload = {
        "username": malicious_email,
        "password": "randompassword" #hacker bu sifreyi salliyor dogrulugu onemli degil
    }

    res = client.post("/login", data=payload)

    assert res.status_code == 403
    assert "Invalid Credentials" in res.json().get("detail", "")

