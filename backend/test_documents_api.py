from app.models import ExtractedDocument, ReadWarning
from app.routers.documents import _document_payload


def test_payload_includes_warnings_with_severity():
    doc = ExtractedDocument(
        file_type="pdf",
        page_count=3,
        warnings=[
            ReadWarning(
                code="SCANNED_PDF",
                message="ไฟล์นี้น่าจะเป็นภาพสแกน",
                severity="error",
            ),
            ReadWarning(
                code="NO_TEXT_LAYER",
                message="หน้า 2 ไม่มีข้อความ",
                page=2,
            ),
        ],
    )
    payload = _document_payload("x.pdf", doc)

    assert payload["warnings"] == [
        {
            "code": "SCANNED_PDF",
            "message": "ไฟล์นี้น่าจะเป็นภาพสแกน",
            "page": None,
            "severity": "error",
        },
        {
            "code": "NO_TEXT_LAYER",
            "message": "หน้า 2 ไม่มีข้อความ",
            "page": 2,
            "severity": "warning",
        },
    ]