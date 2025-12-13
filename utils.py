from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash(password: str):
    return pwd_context.hash(password)

# --- YENİ EKLENEN KISIM ---
def verify(plain_password, hashed_password):
    # Kullanıcının girdiği düz şifreyi (plain), veritabanındaki hash ile karşılaştırır
    return pwd_context.verify(plain_password, hashed_password)

