from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(  #ตัวแอป backend ดึงมาจาก config
    title=settings.app_name,
    version=settings.app_version,
)

# อนุญาตให้หน้าเว็บ (Live Server) เรียก API นี้ได้
app.add_middleware( 
    CORSMiddleware, #ปิดทางให้หน้าเว็บที่รันบน Server เรียก API ได้
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health") #endpoint ทดสอบ
def health_check():
    """ใช้ตรวจว่า backend ทำงานอยู่ และดูกติกาอัปโหลดปัจจุบัน"""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "max_upload_mb": settings.max_upload_mb,
        "allowed_extensions": settings.allowed_extensions,
    }

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import documents          # ← เพิ่ม

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(documents.router)       # ← เพิ่ม: บอก FastAPI ว่ามี endpoint ชุด /api/documents/*

# ... ส่วน /api/health ของเดิมคงไว้เหมือนเดิม