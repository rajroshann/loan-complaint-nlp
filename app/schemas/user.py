from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, Field


class UserCreate(BaseModel):
    """What /signup expects in the request body."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    # EmailStr rejects malformed addresses at the request stage - e.g. "not-an-email"
    # gets a 422 error before your route function ever runs, no manual check needed.


class UserLogin(BaseModel):
    """What /login expects."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """
    What gets sent back after signup/login. Notice: no `password` or
    `hashed_password` field here at all - even though the User table (Step 2)
    has one. If a route accidentally does `return db_user` instead of
    `return UserResponse.model_validate(db_user)`, FastAPI will still only
    serialize the fields declared here, so the hash never leaks out.
    """
    id: int
    email: EmailStr
    created_at: datetime

    # This tells Pydantic "it's fine to build this from a SQLAlchemy object's
    # attributes (user.id, user.email, ...), not just from a plain dict."
    # Without it, passing a SQLAlchemy User object in directly would fail.
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """What /login actually returns to the client - the JWT itself."""
    access_token: str
    token_type: str = "bearer"