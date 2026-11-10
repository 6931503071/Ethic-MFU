from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings                  # แก้: เอา backend. ออก
from app.routers import documents, analysis

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,     # แก้: อ่านรายชื่อจาก config.py
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(analysis.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": settings.app_name}