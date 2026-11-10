from app.ai.redact import Redactor


def test_email_phone_and_id_are_masked_and_restored():
    r = Redactor()
    src = "ติดต่อ somchai.j@mfu.ac.th โทร 081-234-5678 บัตร 1-2345-67890-12-3"
    out = r.redact(src)
    assert "@" not in out
    assert "081" not in out
    assert "67890" not in out
    assert "{{EMAIL_1}}" in out and "{{PHONE_1}}" in out and "{{THAI_ID_1}}" in out
    assert r.restore(out) == src


def test_same_value_gets_same_token():
    r = Redactor()
    out = r.redact("a@b.com และ a@b.com อีกครั้ง")
    assert out.count("{{EMAIL_1}}") == 2
    assert "{{EMAIL_2}}" not in out


def test_titled_names_are_masked():
    r = Redactor()
    out = r.redact("ผู้วิจัยหลัก นางสาวสมหญิง ใจดี และ ผศ.ดร.สมชาย รักเรียน")
    assert "สมหญิง" not in out
    assert "สมชาย" not in out
    assert "{{NAME_1}}" in out


def test_plain_numbers_are_not_masked():
    r = Redactor()
    src = "กลุ่มตัวอย่าง 120 คน งบประมาณ 150,000 บาท ปี พ.ศ. 2569 p < 0.05"
    assert r.redact(src) == src


def test_long_number_and_thai_digits():
    r = Redactor()
    out = r.redact("รหัสนักศึกษา 6931503071 โทร ๐๘๑-๒๓๔-๕๖๗๘")
    assert "6931503071" not in out
    assert "๐๘๑" not in out


def test_unknown_token_from_ai_is_detected():
    r = Redactor()
    r.redact("a@b.com")
    assert r.unknown_tokens("{{EMAIL_1}} {{EMAIL_9}}") == ["{{EMAIL_9}}"]


def test_restore_keeps_unknown_token_and_repr_hides_values():
    r = Redactor()
    r.redact("secret@x.com")
    assert r.restore("{{PHONE_3}}") == "{{PHONE_3}}"
    assert "secret" not in repr(r)
    assert r.summary() == {"EMAIL": 1}


def test_redact_does_not_touch_flag_syntax():
    r = Redactor()
    src = "คำ[[ผิด|เหตุผล]]อยู่ที่นี่"
    assert r.redact(src) == src