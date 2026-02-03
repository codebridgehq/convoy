from fastapi import FastAPI
from src.routes import router

app = FastAPI(title="🚂 Convoy API")

app.include_router(router)