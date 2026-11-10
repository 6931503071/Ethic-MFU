import logging
import tempfile
from dataclasses import asdict
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from config import settings
from app.models import ExtractedDocument
from app.readers.errors import DocumentReadError
from app.readers import read_document
from app.suspects import find_suspects
from app.validators import FileValidationError, validate_upload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


async def _read_upload(file: UploadFile) -> ExtractedDocument:
    content = await file.read()
    try:
        validated = validate_upload(file.filename or "", content)
    except FileValidationError as e:
        raise _error(e.status_code, e.code, e.message)

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{validated.extension}") as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        return await run_in_threadpool(
            read_document, tmp_path, validated.extension.lstrip(".")
        )
    except DocumentReadError as e:
        raise HTTPException(status_code=422, detail=e.to_dict())
    except Exception as e:
        logger.error(f"อ่านเอกสารล้มเหลวโดยไม่คาดคิด: {e}", exc_info=True)
        raise _error(500, "INTERNAL_ERROR", "เกิดข้อผิดพลาดภายในระบบ กรุณาลองใหม่อีกครั้ง")
    finally:
        tmp_path.unlink(missing_ok=True)


def _document_payload(filename: str, doc: ExtractedDocument) -> dict:
    return {
        "filename": filename,
        "file_type": doc.file_type,
        "page_count": doc.page_count,
        "warnings": [asdict(w) for w in doc.warnings],
        "blocks": [
            {
                "index": b.index,
                "text": b.text,
                "kind": b.kind,
                "page": b.page,
            }
            for b in doc.blocks
        ],
    }


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    doc = await _read_upload(file)
    return _document_payload(file.filename, doc)


def build_analysis(filename: str, doc: ExtractedDocument) -> dict:
    payload = _document_payload(filename, doc)
    suspects = [s.to_dict() for s in find_suspects(doc)]
    payload["suspects"] = suspects
    payload["summary"] = {
        "block_count": len(doc.blocks),
        "suspect_count": len(suspects),
        "red_count": sum(1 for s in suspects if s["severity"] == "red"),
        "yellow_count": sum(1 for s in suspects if s["severity"] == "yellow"),
        "is_empty": doc.is_empty,
    }
    return payload

@router.post("/analyze")
async def analyze_document(file: UploadFile = File(...)):
    doc = await _read_upload(file)
    if doc.is_empty:
        raise _error(
            422,
            "NO_TEXT",
            "อ่านไฟล์ได้แต่ไม่พบข้อความ ไฟล์อาจเป็นภาพสแกน (ยังไม่รองรับ OCR)",
        )
    return build_analysis(file.filename, doc)