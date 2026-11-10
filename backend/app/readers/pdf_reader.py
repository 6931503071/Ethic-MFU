"""ตัวอ่านไฟล์ PDF
อ่านทีละหน้าด้วย PyMuPDF เก็บเลขหน้าไว้ในทุก Block
คลีนอักขระสี่เหลี่ยมแปลกปลอม รักษาสระและวรรณยุกต์ไทยครบถ้วน
"""

import re
import unicodedata
from pathlib import Path

import pymupdf
from app.models import Block, ExtractedDocument, ReadWarning
from app.readers.errors import DocumentReadError

# สัญญาณว่า PDF ถอดรหัสฟอนต์ไม่ได้
_CID_PATTERN = re.compile(r"\(cid:\d+\)")
_BOX_CHARS_PATTERN = re.compile(r"[□■\uFFFD\u200B\uFEFF]")

# สัญญาณเพี้ยนจริง (ไม่รวม \u200B \uFEFF ซึ่งเป็นตัวไม่แสดงผลที่ลบได้ปกติ)
_SIGNAL_CHARS_PATTERN = re.compile(r"[□■\uFFFD]")


def count_garble_signals(text: str) -> int:
    """นับสัญญาณข้อความเพี้ยนจากข้อความดิบ ต้องเรียกก่อน sanitize_text"""
    if not text:
        return 0
    return len(_CID_PATTERN.findall(text)) + len(_SIGNAL_CHARS_PATTERN.findall(text))


def sanitize_text(text: str) -> str:
    """1. ทำความสะอาดข้อความ ลบสี่เหลี่ยม โดยคงสระและวรรณยุกต์ไทยไว้ครบ 100%"""
    if not text:
        return ""

    # 1.1 ปรับ normalization เป็น NFC เพื่อผสานสระและวรรณยุกต์ลอยให้สมบูรณ์
    text = unicodedata.normalize("NFC", text)

    # 1.2 ลบ CID และสัญลักษณ์สี่เหลี่ยมแปลกปลอม
    text = _CID_PATTERN.sub("", text)
    text = _BOX_CHARS_PATTERN.sub("", text)

    # 1.3 กรองเฉพาะ Control Characters ตัวปัญหา (Cc, Co) แต่คงสระ/วรรณยุกต์ (Mn, Mc) ไว้ทั้งหมด
    cleaned_chars = []
    for char in text:
        cat = unicodedata.category(char)
        if cat in ("Cc", "Co") and char not in ("\n", "\r", "\t"):
            continue
        cleaned_chars.append(char)

    return "".join(cleaned_chars)


def format_thai_text(text: str) -> str:
    """2. จัดระเบียบข้อความ และเว้นวรรค"""
    text = sanitize_text(text)

    #ยุบช่องว่างซ้ำซ้อนให้เหลือเว้นวรรคเดียว
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def _looks_garbled(text: str) -> bool:
    """ใช้กับข้อความดิบเท่านั้น (ก่อน sanitize)"""
    return count_garble_signals(text) > 0


def read_pdf(path: Path) -> ExtractedDocument:
    """อ่านไฟล์ PDF ที่ path แล้วคืน ExtractedDocument"""
    try:
        pdf = pymupdf.open(str(path))
    except Exception as exc:
        error_text = repr(exc).lower()
        if "password" in error_text or "encrypt" in error_text:
            raise DocumentReadError(
                "PDF_ENCRYPTED",
                "ไฟล์ PDF นี้ติดรหัสผ่าน กรุณาปลดรหัสผ่านแล้วอัปโหลดใหม่",
                message_en="This PDF is password-protected. Please remove the password and upload it again.",
            ) from exc
        raise DocumentReadError(
            "PDF_CORRUPT",
            "ไม่สามารถเปิดไฟล์ PDF ได้ ไฟล์อาจเสียหายหรือไม่ใช่ไฟล์ PDF ที่ถูกต้อง",
            message_en="Could not open this PDF. The file may be damaged or is not a valid PDF.",
        ) from exc

    # PyMuPDF เปิดไฟล์ที่ติดรหัสผ่านได้โดยไม่ error ต้องเช็กแยก
    if pdf.needs_pass:
        pdf.close()
        raise DocumentReadError(
            "PDF_ENCRYPTED",
            "ไฟล์ PDF นี้ติดรหัสผ่าน กรุณาปลดรหัสผ่านแล้วอัปโหลดใหม่",
            message_en="This PDF is password-protected. Please remove the password and upload it again.",
        )

    blocks: list[Block] = []
    warnings: list[ReadWarning] = []
    with pdf: 
        page_count = pdf.page_count
        for page_number, page in enumerate(pdf, start=1):
            try:
                text = page.get_text() or ""
            except Exception:
                warnings.append(
                    ReadWarning(
                        code="PAGE_READ_FAILED",
                        message=f"อ่านหน้า {page_number} ไม่สำเร็จ เนื้อหาหน้านี้ไม่ได้ถูกนำเข้า",
                        page=page_number,
                    )
                )
                continue

            if not text.strip():
                warnings.append(
                    ReadWarning(
                        code="NO_TEXT_LAYER",
                        message=(
                            f"หน้า {page_number} ไม่มีข้อความที่อ่านได้ "
                            "อาจเป็นภาพสแกน (ต้องใช้ OCR) หรือเป็นหน้าว่าง"
                        ),
                        page=page_number,
                    )
                )
                continue

            if _looks_garbled(text):
                warnings.append(
                    ReadWarning(
                        code="GARBLED_TEXT",
                        message=(
                            f"หน้า {page_number} มีอักขระที่ถอดรหัสไม่ได้ "
                            "ข้อความอาจเพี้ยน แนะนำให้ใช้ไฟล์ DOCX แทน"
                        ),
                        page=page_number,
                    )
                )

            # คลีนข้อความ จัดการสระ วรรณยุกต์ และเว้นวรรคภาษาไทยก่อนแยกก้อน Block
            cleaned_text = format_thai_text(text)

            # แยกก้อนตามบรรทัดว่าง
            for part in re.split(r"\n\s*\n", cleaned_text):
                part_text = part.strip()
                if part_text:
                    blocks.append(
                        Block(
                            index=len(blocks),
                            text=part_text,
                            kind="paragraph",
                            page=page_number,
                        )
                    )

    result = ExtractedDocument(
        file_type="pdf",
        page_count=page_count,
        blocks=blocks,
        warnings=warnings,
    )
    pages_without_text = [
        w.page for w in warnings if w.code == "NO_TEXT_LAYER"
    ]
    if page_count and len(pages_without_text) / page_count > 0.5:
        result.warnings.append(
            ReadWarning(
                code="SCANNED_PDF",
                message=(
                    "ไฟล์นี้น่าจะเป็นภาพสแกน ระบบยังไม่รองรับ OCR "
                    "กรุณาอัปโหลดไฟล์ DOCX หรือ PDF ที่เลือกข้อความได้"
                ),
                severity="error",
            )
        )

    if result.is_empty:
        result.warnings.append(
            ReadWarning(
                code="EMPTY_DOCUMENT",
                message="เปิดไฟล์ได้ แต่ไม่พบข้อความเลย อาจเป็น PDF ที่สแกนมาทั้งไฟล์",
            )
        )

    return result

