from pathlib import Path

import pymupdf

from app.readers import read_document
from app.readers.pdf_reader import (
    _looks_garbled,
    count_garble_signals,
    read_pdf,
    sanitize_text,
)

FIXTURE = Path(__file__).resolve().parent / "tests" / "fixtures" / "ap02_th.pdf"


def _make_image_only_pdf(path: Path, pages: int = 3) -> None:
    """สร้าง PDF ที่มีแต่รูป ไม่มี text layer (จำลองไฟล์สแกน)"""
    doc = pymupdf.open()
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 200, 200), False)
    pix.clear_with(255)
    for _ in range(pages):
        page = doc.new_page()
        page.insert_image(page.rect, pixmap=pix)
    doc.save(str(path))
    doc.close()


def test_thai_words_extracted_correctly():
    doc = read_pdf(FIXTURE)
    full = "\n".join(b.text for b in doc.blocks)
    assert "ระบุห้อง" in full
    assert "ทำให้สนใจ" in full
    assert "ระบหุ ้อง" not in full
    assert "ทำใหส้ นใจ" not in full


def test_does_not_merge_field_lines():
    doc = read_pdf(FIXTURE)
    full = "\n".join(b.text for b in doc.blocks)
    assert "ผู้ประสานงานโครงการวิจัยเบอร์โทรศัพท์" not in full


def test_no_warnings_on_text_pdf():
    doc = read_pdf(FIXTURE)
    assert doc.page_count == 15
    assert doc.warnings == []


def test_scanned_pdf_is_flagged(tmp_path):
    scanned = tmp_path / "scan.pdf"
    _make_image_only_pdf(scanned)
    doc = read_pdf(scanned)
    assert "SCANNED_PDF" in [w.code for w in doc.warnings]


def test_scanned_warning_has_error_severity(tmp_path):
    scanned = tmp_path / "scan.pdf"
    _make_image_only_pdf(scanned)
    doc = read_pdf(scanned)
    w = next(w for w in doc.warnings if w.code == "SCANNED_PDF")
    assert w.severity == "error"



def test_thai_marks_not_lost_on_ap02():
    fixture = Path(__file__).parent / "tests" / "fixtures" / "ap02_th.pdf"
    text = "".join(b.text for b in read_document(fixture, "pdf").blocks)

    assert sum(text.count(c) for c in "\u0e48\u0e49\u0e4a\u0e4b") == 1006  # วรรณยุกต์
    assert text.count("\u0e4c") == 115  # ทัณฑฆาต
    assert text.count("\u0e33") == 97   # สระอำ
    assert text.count("\u0e4d") == 0    # นิคหิตที่แยกออกมา



def test_garble_signals_detected_before_sanitize():
    raw = "ระบุ\uFFFDห้อง (cid:12) □"
    assert count_garble_signals(raw) == 3
    assert _looks_garbled(raw)
    # หลัง sanitize สัญญาณหายหมด จึงต้องตรวจก่อนเสมอ
    assert not _looks_garbled(sanitize_text(raw))