"""
ตัวอ่านไฟล์ DOCX

อ่านย่อหน้าและตารางตามลำดับที่ปรากฏในเอกสารจริง
แล้วคืนเป็น ExtractedDocument (โครงสร้างกลางใน models.py)
"""

from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.models import Block, ExtractedDocument, ReadWarning
from app.readers.errors import DocumentReadError


def _is_heading(paragraph: Paragraph) -> bool:
    """ย่อหน้านี้เป็นหัวข้อหรือไม่ ดูจากชื่อ style ของ Word"""
    style_name = paragraph.style.name if paragraph.style is not None else ""
    return style_name.startswith(("Heading", "Title"))


def _iter_body(doc):
    """
    วนอ่านส่วนเนื้อหาของเอกสารตามลำดับจริง
    คืนค่าเป็น Paragraph หรือ Table ทีละชิ้น

    python-docx มี doc.paragraphs กับ doc.tables แยกกัน ถ้าใช้สองอันนี้ตรง ๆ
    ลำดับจะเพี้ยน จึงต้องวนจาก XML ของ body โดยตรง
    """
    for child in doc.element.body.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, doc)
        elif child.tag == qn("w:tbl"):
            yield Table(child, doc)


def read_docx(path: Path) -> ExtractedDocument:
    """อ่านไฟล์ DOCX ที่ path แล้วคืน ExtractedDocument"""
    try:
        doc = Document(str(path))
    except Exception as exc:
        raise DocumentReadError(
            "DOCX_CORRUPT",
            "ไม่สามารถเปิดไฟล์ DOCX ได้ ไฟล์อาจเสียหายหรือไม่ใช่ไฟล์ Word ที่ถูกต้อง",
            message_en="Could not open this DOCX. The file may be damaged or is not a valid Word file.",
        ) from exc

    blocks: list[Block] = []
    warnings: list[ReadWarning] = []

    def add_block(text: str, kind: str) -> None:
        # ข้ามก้อนที่ว่างจริง ๆ แต่ไม่แก้ข้อความของก้อนที่มีเนื้อหา
        if text.strip():
            blocks.append(Block(index=len(blocks), text=text, kind=kind, page=None))

    for item in _iter_body(doc):
        if isinstance(item, Paragraph):
            kind = "heading" if _is_heading(item) else "paragraph"
            add_block(item.text, kind)
        else:  # Table
            for row in item.rows:
                seen_cells = set()  # เซลล์ที่ merge จะโผล่ซ้ำ ใช้ id ของ XML กรองซ้ำ
                for cell in row.cells:
                    cell_id = id(cell._tc)
                    if cell_id in seen_cells:
                        continue
                    seen_cells.add(cell_id)
                    add_block(cell.text, "table_cell")

    result = ExtractedDocument(
        file_type="docx",
        page_count=None,
        blocks=blocks,
        warnings=warnings,
    )

    if result.is_empty:
        result.warnings.append(
            ReadWarning(
                code="EMPTY_DOCUMENT",
                message="เปิดไฟล์ได้ แต่ไม่พบข้อความในเอกสาร อาจเป็นไฟล์ที่มีแต่รูปภาพ",
            )
        )

    return result