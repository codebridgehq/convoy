from fastapi import FastAPI
from src.routes import router

app = FastAPI(title="🚂 Convoy API", description="Simplified batch processing")

app.include_router(router)