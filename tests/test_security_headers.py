import pytest

def test_security_headers_present(client):

    res = client.get("/")
    assert res.status_code == 200
    res_headers = res.headers
    assert res_headers.get("X-Content-Type-Options") == "nosniff", "X-Content-Type-Options header eksik veya yanlış"
    assert res_headers.get("X-Frame-Options") == "DENY", "X-Frame-Options header eksik veya yanlış"
    
