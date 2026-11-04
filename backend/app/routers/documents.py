import uuid
from pathlib import PurePath

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from app.config import settings
from app.validators import FileValidationError, validate_upload

router = APIRouter(prefix="/api/documents", tags=["documents"])

CHUNK_SIZE = 1024 * 1024  # อ่านทีละ 1 MB


async def _read_limited(file: UploadFile) -> bytes:
    """อ่านไฟล์ทีละก้อน และหยุดทันทีเมื่อเกินขนาดที่กำหนด
    เพื่อไม่ให้ไฟล์ใหญ่ๆ กินหน่วยความจำของเซิร์ฟเวอร์"""
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > settings.max_upload_bytes:
            raise FileValidationError(
                "FILE_TOO_LARGE",
                f"ไฟล์ใหญ่เกินกำหนด ระบบรับไฟล์ไม่เกิน {settings.max_upload_mb} MB",
                status_code=413,
            )
        chunks.append(chunk)
    return b"".join(chunks)


def _error_response(err: FileValidationError) -> JSONResponse:
    # รูปแบบ error เดียวกันทุกกรณี หน้าเว็บใช้ code แยกแยะ และแสดง message ให้ผู้ใช้
    return JSONResponse(
        status_code=err.status_code,
        content={"error": {"code": err.code, "message": err.message}},
    )


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        content = await _read_limited(file)
        validated = validate_upload(file.filename or "", content)
    except FileValidationError as err:
        return _error_response(err)
    finally:
        await file.close()

    # ตั้งชื่อไฟล์บนดิสก์เองด้วยรหัสสุ่ม ไม่ใช้ชื่อที่ผู้ใช้ส่งมา
    document_id = uuid.uuid4().hex
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    saved_path = settings.upload_dir / f"{document_id}{validated.extension}"
    saved_path.write_bytes(content)

    return {
        "document_id": document_id,
        "filename": PurePath(file.filename or "").name,
        "extension": validated.extension,
        "size_bytes": validated.size_bytes,
    }