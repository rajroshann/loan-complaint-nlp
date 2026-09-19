# You do not run database.py or models.py directly in the terminal. They are setup files, not execution files.Instead, they are designed to be imported and run by other files (like the create_tables.py script you created).Here is the exact order of operations so you know precisely when they are used:

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)  # never store the raw password - Step 4 handles hashing
    created_at = Column(DateTime, default=datetime.utcnow)

    # This doesn't create a database column - it's a Python-side convenience.
    # It lets you write `some_user.predictions` in code to get all of that
    # user's rows from the predictions table, without writing a JOIN query
    # by hand every time.
    predictions = relationship("Prediction", back_populates="owner")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    complaint_text = Column(String, nullable=False)
    predicted_label = Column(String, nullable=False)     # e.g. "Relief" / "No Relief"
    confidence = Column(Float, nullable=False)             # e.g. 0.82
    created_at = Column(DateTime, default=datetime.utcnow)

    # The other side of the relationship above - lets you write
    # `some_prediction.owner.email` to get back to the user who made it.
    owner = relationship("User", back_populates="predictions")