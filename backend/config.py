from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent  # โฟลเดอร์ backend/

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
    ai_model: str = "claude-sonnet-5-5"       # ชื่อโมเดล เปลี่ยนได้ใน .env (AI_MODEL=...)
    ai_timeout_seconds: float = 120.0         # รอ AI นานสุดต่อ 1 ครั้งที่เรียก เกินแล้วแจ้ง AI_TIMEOUT
    ai_max_input_chars: int = 60000           # ข้อความสูงสุดที่ส่งให้ AI ต่อครั้ง (เกิน = แจ้งผู้ใช้)
    ai_max_output_tokens: int = 16000
    ai_chunk_chars: int = 100000              # ไฟล์ยาว: แบ่งให้ AI หาส่วนที่เกี่ยวข้องทีละก้อนขนาดนี้
    ai_max_chunks: int = 12                   # เกินนี้แจ้งว่าไฟล์ยาวเกินไป
    ai_locate_workers: int = 3                # เรียก AI หาส่วนที่เกี่ยวข้องพร้อมกันกี่ก้อน

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


settings = Settings()#ตัวแปร settings จะเก็บค่าต่าง ๆ ที่อ่านจากไฟล์ .env และค่าดีฟอลต์ที่กำหนดไว้ในคลาส Settings