from app.readers.errors import DocumentReadError  # ปรับ path ให้ตรงกับที่ไฟล์ error.py อยู่จริง


def test_error_with_both_languages():
    err = DocumentReadError(
        "PDF_ENCRYPTED",
        "ไฟล์ PDF ติดรหัสผ่าน",
        message_en="This PDF is password-protected.",
    )
    assert err.to_dict() == {
        "code": "PDF_ENCRYPTED",
        "message": "ไฟล์ PDF ติดรหัสผ่าน",
        "message_th": "ไฟล์ PDF ติดรหัสผ่าน",
        "message_en": "This PDF is password-protected.",
    }


def test_old_two_argument_form_still_works():
    err = DocumentReadError("DOCX_CORRUPT", "ไฟล์ DOCX เสียหาย")
    d = err.to_dict()

    assert err.message == "ไฟล์ DOCX เสียหาย"
    assert d["message"] == d["message_th"] == "ไฟล์ DOCX เสียหาย"
    assert d["message_en"]  # ไม่ว่าง แม้ยังไม่ได้ใส่ภาษาอังกฤษ