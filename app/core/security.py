# # password hashing, JWT create/verify

from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError

from app.core.config import settings

# CryptContext handles the actual bcrypt hashing/verification for you -
# you never call bcrypt functions directly, just these two methods.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Turn a plain-text password into its bcrypt hash, for storing in the DB."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check a login attempt's password against the stored hash.
    Returns True/False - never reveals or reconstructs the original password.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int) -> str:
    """
    Build and sign a JWT for a logged-in user. `sub` (subject) is the JWT
    standard field name for "who this token is about" - we store the
    user's DB id there as a string (JWT spec requires `sub` to be a string).
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """
    Verify a token's signature and expiry, and return the user_id inside it.
    Returns None if the token is invalid, tampered with, or expired -
    the route calling this (Step 5+) will turn that into a 401 error.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        return int(user_id) if user_id else None
    except JWTError:
        return None


if __name__ == "__main__":
    # Quick manual check — run this file directly to confirm hashing and
    # tokens both work end-to-end before anything else depends on them.
    pw = "testpass123"
    hashed = hash_password(pw)
    print("Hashed password:", hashed)
    print("Correct password verifies:", verify_password(pw, hashed))
    print("Wrong password verifies  :", verify_password("wrongpass", hashed))

    token = create_access_token(user_id=42)
    print("\nJWT:", token)
    print("Decoded user_id:", decode_access_token(token))
    print("Tampered token decodes to:", decode_access_token(token + "tampered"))