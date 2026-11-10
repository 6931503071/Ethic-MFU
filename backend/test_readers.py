"""ทดสอบตัวอ่าน DOCX/PDF โดยสร้างไฟล์ตัวอย่างชั่วคราวขึ้นเอง"""

import tempfile
from pathlib import Path

from docx import Document
from PIL import Image

from app.readers import read_document
from app.readers.errors import DocumentReadError


def _expect_error(path: Path, file_type: str, code: str) -> None:
    try:
        read_document(path, file_type)
    except DocumentReadError as exc:
        assert exc.code == code, f"ได้รหัส {exc.code} แต่ต้องการ {code}"
        return
    raise AssertionError("ควรเกิด DocumentReadError แต่ไม่เกิด")


def test_docx_order_kinds_and_merged_cells():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "sample.docx"
        doc = Document()
        doc.add_heading("หัวข้อทดสอบ", level=1)
        doc.add_paragraph("ย่อหน้าแรก")

        table = doc.add_table(rows=2, cols=2)
        table.cell(0, 0).text = "A1"
        table.cell(0, 1).text = "B1"
        table.cell(1, 0).merge(table.cell(1, 1)).text = "รวมเซลล์"

        doc.add_paragraph("ย่อหน้าหลังตาราง")
        doc.add_paragraph("")  # ย่อหน้าว่าง ต้องถูกข้าม
        doc.save(path)

        result = read_document(path, "docx")
        assert [b.text for b in result.blocks] == [
            "หัวข้อทดสอบ",
            "ย่อหน้าแรก",
            "A1",
            "B1",
            "รวมเซลล์",
            "ย่อหน้าหลังตาราง",
        ]
        assert [b.kind for b in result.blocks] == [
            "heading",
            "paragraph",
            "table_cell",
            "table_cell",
            "table_cell",
            "paragraph",
        ]
        assert [b.index for b in result.blocks] == list(range(6))
        assert result.warnings == []


def test_docx_empty_gives_warning():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "empty.docx"
        Document().save(path)

        result = read_document(path, "docx")
        assert result.is_empty
        assert [w.code for w in result.warnings] == ["EMPTY_DOCUMENT"]


def test_docx_corrupt():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "bad.docx"
        path.write_text("ไม่ใช่ไฟล์ Word", encoding="utf-8")

        _expect_error(path, "docx", "DOCX_CORRUPT")


def test_pdf_image_only_gives_no_text_warning():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "scan.pdf"
        Image.new("RGB", (300, 300), "white").save(path, "PDF")

        result = read_document(path, "pdf")
        codes = [w.code for w in result.warnings]
        assert result.page_count == 1
        assert result.is_empty
        assert "NO_TEXT_LAYER" in codes
        assert "EMPTY_DOCUMENT" in codes


def test_pdf_corrupt():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "bad.pdf"
        path.write_bytes(b"this is not a pdf")

        _expect_error(path, "pdf", "PDF_CORRUPT")


def test_unsupported_type():
    _expect_error(Path("x.txt"), "txt", "UNSUPPORTED_TYPE")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ผ่าน", name)
    print("ทดสอบครบทุกข้อ")