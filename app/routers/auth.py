from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # pulls back the auto-generated id/created_at from the DB
    return new_user  # UserResponse's from_attributes config (Step 3) handles the conversion


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()

    # Deliberately the SAME error for "no such email" and "wrong password" -
    # a different message for each would let an attacker discover which
    # emails are registered just by trying logins. Never split this in two.
    invalid_error = HTTPException(status_code=401, detail="Invalid email or password")

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise invalid_error

    token = create_access_token(user_id=user.id)
    return Token(access_token=token)