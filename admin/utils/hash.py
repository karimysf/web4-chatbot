from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

pass_hasher = PasswordHasher()

def hash_password(password: str) -> str:
    return pass_hasher.hash(password)

def verify_password(hashed_password: str, password: str) -> bool:
    try:
        return pass_hasher.verify(hashed_password, password)
    except VerifyMismatchError:
        return False
    


def is_hashed(password: str) -> bool:
    """Check if the password is already hashed (Argon2 format)"""
    return password.startswith("$argon2id$")



print(f"admin email hashed :{hash_password("admin123")}")
print(f"apprenant email: final@gmail.com password: app123 ")