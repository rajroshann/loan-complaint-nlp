from fastapi import FastAPI

from app.db.database import Base, engine
from app.db import models  # noqa: F401 — registers tables with Base before create_all runs
from fastapi.staticfiles import StaticFiles
from app.routers import auth, predict,history,pages  # add predict here and history here

# Ensures tables exist every time the server starts - safe to call repeatedly,
# it does nothing if they already exist. Means you no longer need to
# separately run create_tables.py after this point.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Loan Complaint NLP API")

app.include_router(auth.router)
app.include_router(predict.router)      # add this line
app.include_router(history.router)                # add this line
app.include_router(pages.router)                          # add this line

app.mount("/static", StaticFiles(directory="static"), name="static")   # add this line, after include_router calls

@app.get("/health")
def health_check():
    return {"status": "ok"}

# . app/main.py (The Central Hub)What it does: This is the absolute entry point and brain of your whole application.How it relates to your project: When you launch your app, this file runs first. It ensures all your database tables exist automatically (meaning you no longer need that old create_tables.py script!). It then turns on the FastAPI framework, plugs in the authentication paths you wrote, and exposes a simple /health path to confirm your server is alive and well.