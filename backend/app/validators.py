import io
import zipfile
from dataclasses import dataclass
from pathlib import PurePath

from app.config import settings

PDF_SIGNATURE = b"%PDF-"
ZIP_SIGNATURE = b"PK\x03\x04"
OLE_SIGNATURE = b"\xd0\xcf\x11\xe0"  # ไฟล์ Word เก่า (.doc) หรือไฟล์ที่ใส่รหัสผ่าน

# กันไฟล์ DOCX ที่บีบอัดมาให้พองตัวมหาศาลเมื่อแตกไฟล์ (zip bomb)
MAX_ZIP_ENTRIES = 2000
MAX_UNZIPPED_BYTES = 100 * 1024 * 1024


class FileValidationError(Exception):
    """ไฟล์ไม่ผ่านการตรวจสอบ: มี code ให้โปรแกรมใช้ และ message ให้ผู้ใช้อ่าน"""

    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


@dataclass(frozen=True)
class ValidatedFile:
    extension: str
    size_bytes: int


def _get_extension(filename: str) -> str:
    # PurePath(...).name ตัดพาธออก เหลือแต่ชื่อไฟล์ (กันชื่อแปลกๆ เช่น ../../x.pdf)
    name = PurePath(filename or "").name
    return PurePath(name).suffix.lower()


def _check_pdf(content: bytes) -> None:
    # PDF จริงต้องมี %PDF- อยู่ต้นไฟล์ (ข้อกำหนดอนุโลมให้อยู่ใน 1024 ไบต์แรก)
    if PDF_SIGNATURE not in content[:1024]:
        raise FileValidationError(
            "INVALID_PDF",
            "ไฟล์นี้ไม่ใช่ PDF ที่แท้จริง หรือไฟล์เสียหาย "
            "กรุณาตรวจสอบไฟล์แล้วลองอัปโหลดใหม่",
        )


def _check_docx(content: bytes) -> None:
    if content.startswith(OLE_SIGNATURE):
        raise FileValidationError(
            "UNSUPPORTED_OR_ENCRYPTED_DOCX",
            "ไฟล์นี้เป็น Word รุ่นเก่า (.doc) หรือถูกใส่รหัสผ่าน "
            "กรุณาเปิดใน Word แล้วบันทึกเป็น .docx แบบไม่มีรหัสผ่าน",
        )

    if not content.startswith(ZIP_SIGNATURE):
        raise FileValidationError(
            "INVALID_DOCX",
            "ไฟล์นี้ไม่ใช่ DOCX ที่แท้จริง หรือไฟล์เสียหาย "
            "กรุณาตรวจสอบไฟล์แล้วลองอัปโหลดใหม่",
        )

    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            entries = zf.infolist()
            names = {entry.filename for entry in entries}

            if len(entries) > MAX_ZIP_ENTRIES:
                raise FileValidationError(
                    "DOCX_TOO_COMPLEX", "โครงสร้างไฟล์ DOCX ซับซ้อนผิดปกติ จึงไม่รับไฟล์นี้"
                )
            if sum(entry.file_size for entry in entries) > MAX_UNZIPPED_BYTES:
                raise FileValidationError(
                    "DOCX_TOO_LARGE_UNZIPPED", "เนื้อหาในไฟล์ DOCX มีขนาดใหญ่ผิดปกติ จึงไม่รับไฟล์นี้"
                )
            # DOCX จริงต้องมีสองส่วนนี้เสมอ
            if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                raise FileValidationError(
                    "INVALID_DOCX",
                    "ไฟล์นี้ไม่ใช่เอกสาร Word (.docx) ที่แท้จริง "
                    "กรุณาตรวจสอบไฟล์แล้วลองอัปโหลดใหม่",
                )
    except zipfile.BadZipFile:
        raise FileValidationError(
            "CORRUPTED_FILE", "ไฟล์ DOCX เสียหาย ไม่สามารถเปิดอ่านได้"
        )


# เพิ่มชนิดไฟล์ใหม่ในอนาคตได้ที่นี่ที่เดียว
SIGNATURE_CHECKERS = {
    ".pdf": _check_pdf,
    ".docx": _check_docx,
}


def validate_upload(filename: str, content: bytes) -> ValidatedFile:
    """ตรวจไฟล์ตามลำดับ: นามสกุล -> ไม่ว่าง -> ขนาด -> ลายเซ็นไฟล์จริง"""
    extension = _get_extension(filename)

    if extension not in settings.allowed_extensions or extension not in SIGNATURE_CHECKERS:
        allowed = ", ".join(e.upper().lstrip(".") for e in settings.allowed_extensions)
        raise FileValidationError(
            "UNSUPPORTED_FILE_TYPE",
            f"ไม่รองรับไฟล์ชนิดนี้ ระบบรับเฉพาะ {allowed}",
            status_code=415,
        )

    size = len(content)

    if size == 0:
        raise FileValidationError("EMPTY_FILE", "ไฟล์ว่างเปล่า ไม่มีเนื้อหาให้อ่าน")

    if size > settings.max_upload_bytes:
        raise FileValidationError(
            "FILE_TOO_LARGE",
            f"ไฟล์ใหญ่เกินกำหนด ระบบรับไฟล์ไม่เกิน {settings.max_upload_mb} MB",
            status_code=413,
        )

    SIGNATURE_CHECKERS[extension](content)

    return ValidatedFile(extension=extension, size_bytes=size)