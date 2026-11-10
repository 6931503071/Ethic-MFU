"""ทางเข้าเดียวของการอ่านเอกสาร
ส่วนอื่นของโปรแกรมเรียกแค่ read_document() โดยไม่ต้องรู้ว่าไฟล์เป็นชนิดไหน
จะเพิ่มตัวอ่านชนิดใหม่ ให้เขียนไฟล์ reader ใหม่แล้วเพิ่มลง _READERS ที่เดียว
"""

from pathlib import Path

from app.models import ExtractedDocument
from app.readers.docx_reader import read_docx
from app.readers.errors import DocumentReadError
from app.readers.pdf_reader import read_pdf

_READERS = {
    "pdf": read_pdf,
    "docx": read_docx,
}


def read_document(path: Path, file_type: str) -> ExtractedDocument:
    """เลือกตัวอ่านตามชนิดไฟล์ ("pdf" หรือ "docx") แล้วคืน ExtractedDocument"""
    reader = _READERS.get(file_type.lower().lstrip("."))
    if reader is None:
        raise DocumentReadError(
            "UNSUPPORTED_TYPE",
            f"ยังไม่รองรับการอ่านไฟล์ชนิด {file_type}",
            message_en=f"Reading {file_type} files is not supported yet.",
        )
    return reader(path)


__all__ = ["read_document", "DocumentReadError"]