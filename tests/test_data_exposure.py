import pytest
from app import schemas

def test_no_password_in_response(client, test_user):
    
    res = client.get(f"/users/{test_user['id']}")
    assert res.status_code == 200

    data = res.json()
    assert "password" not in data, "guvenlik acigi: password alani donuyor"

def test_correct_response_model(client, test_user):
    res = client.get(f"/users/{test_user['id']}")

    try:
        schemas.UserOut(**res.json())
    except Exception as e:
        pytest.fail(f"Response modeli UserOut'a uymuyor: {e}")


    