import pytest
from app import models

def test_user_cannot_update_role_via_profile_update(authorized_client, test_user, session):
    payload = {
        "email": "hacker@mail.com",
        "password": "123456789",
        "role": "admin"  # Kötü niyetli kullanıcı rolünü değiştirmeye çalışıyor
    }
    res = authorized_client.put(f"/users/{test_user['id']}", json=payload)

    updated_user = session.query(models.User).filter(models.User.id == test_user['id']).first()
    
    assert updated_user.role == "user"
