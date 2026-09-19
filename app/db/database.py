# You do not run database.py or models.py directly in the terminal. They are setup files, not execution files.Instead, they are designed to be imported and run by other files (like the create_tables.py script you created).Here is the exact order of operations so you know precisely when they are used:

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

# The "engine" is the actual connection to the database file/server.
# connect_args is SQLite-specific: by default SQLite only allows the thread
# that created a connection to use it, which breaks under FastAPI's async
# request handling. This flag turns that restriction off. (Skip this arg
# entirely if you ever switch to PostgreSQL - it doesn't apply there.)
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

# SessionLocal is a factory that creates new "conversations" with the database.
# Think of `engine` as the phone line, and each Session as one phone call -
# you open one per request, do your reads/writes, then hang up.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is what every table model (in models.py) will inherit from - it's how
# SQLAlchemy knows "this Python class corresponds to a database table."
Base = declarative_base()


def get_db():
    """
    A FastAPI dependency: opens one database session per request, hands it
    to whichever route function asks for it, and guarantees it's closed
    afterward - even if that route raises an error. You'll plug this into
    routes with `db: Session = Depends(get_db)` starting in Step 5.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()