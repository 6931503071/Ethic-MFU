from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent #อ้างอิงตำแหน่งโฟลเดอร์ backend/

class Settings(BaseSettings):
    # ข้อมูลทั่วไปของแอป
    app_name: str = "Ethic-MFU Document Generator"
    app_version: str = "0.1.0"

    # การอัปโหลดไฟล์
    max_upload_mb: int = 10 #บอกว่า รองรับไฟล์ขนาดสูงสุด 10 MB
    allowed_extensions: list[str] = [".pdf", ".docx"] #อ่านแค่ไฟล์ประเภท PDF, DOCX, TXT จากที่นี่ที่เดียว

    # ไฟล์ชั่วคราว (ต้องลบหลังประมวลผลเสร็จ)
    upload_dir: Path = BASE_DIR / "tmp_uploads" #รองรับความเป็นส่วนตัว ไฟล์ชั่วคราวจะถูกเก็บไว้ในโฟลเดอร์ tmp_uploads
    file_retention_minutes: int = 30

    # หน้าเว็บที่อนุญาตให้เรียก API (Live Server ของ VS Code ใช้พอร์ต 5500)
    cors_origins: list[str] = [
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ]

    # กุญแจ AI: ห้ามใส่ในโค้ด ให้ใส่ในไฟล์ .env เท่านั้น
    ai_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


settings = Settings()#ตัวแปร settings จะเก็บค่าต่าง ๆ ที่อ่านจากไฟล์ .env และค่าดีฟอลต์ที่กำหนดไว้ในคลาส Settings