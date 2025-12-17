from pydantic import BaseModel, EmailStr, field_validator, Field
from datetime import datetime
from typing import Optional

# Post Şemaları
class PostBase(BaseModel):
    title: str
    content: str
    published: bool = True

class PostCreate(PostBase):
    pass

class Post(PostBase):
    id: int
    created_at: datetime
    # Owner_id ileride eklenecek
    owner_id: int
    class Config:
        from_attributes = True
    

# User Şemaları
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime
    class Config:
        from_attributes = True

#Login Semasi
class UserLogin(BaseModel):
    email: EmailStr
    password: str

#Token Semasi
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    id: Optional[str] = None

class Vote(BaseModel):
    post_id: int
    dir: int # 1 = Like, 0 = Unlike

    # Pydantic V2 Kullanımı:
    @field_validator('dir')
    @classmethod
    def validate_dir(cls, v: int):
        if v not in [0, 1]:
            raise ValueError('dir must be 0 or 1 (0=Unlike, 1=Like)')
        return v
    
# Post ve Beğeni Sayısını beraber döndüren şema
class PostOut(BaseModel):
    Post: Post # Daha önce tanımladığımız Post şeması
    votes: int # Beğeni sayısı

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)

    class Config:
        # Örnek bir veri yapısı göstererek dökümantasyonu (Swagger) güzelleştirirsin
        schema_extra = {
            "example": {
                "email": "yeniemail@example.com",
                "password": "guclu_sifre_123"
            }
        }

    

