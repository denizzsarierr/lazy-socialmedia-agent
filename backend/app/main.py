from fastapi import FastAPI
from sqlalchemy import text

from .database import engine

app = FastAPI(
    title = "LazyAI Instagram Agent",
    version = "0.1.0"
)

@app.get("/health")
def healt():

    return {
        "status": "ok"
    }

@app.get("/db-test")
def db_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar()

    return {
        "database": "connected",
        "result": value,
    }