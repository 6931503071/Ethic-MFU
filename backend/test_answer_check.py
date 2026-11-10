"""ทดสอบตัวตรวจคำตอบ AI (app/ai/answer_check.py) รันจาก backend/: python3 -m pytest -q"""
from pathlib import Path

from app.ai.answer_check import apply_accepted, check_answers, normalize_for_compare
from app.ai.redact import Redactor
from app.filled_form import FilledForm, ValueStatus
from app.form_fields import load_template

T = load_template(Path(__file__).resolve().parent / "ap02.json")

BLOCKS = {
    0: "ผลของการออกกำลังกายต่อความดันโลหิต",
    1: "เพื่อศึกษาผลของการเดินเร็วต่อความดันโลหิต",
    2: "เพื่อเปรียบเทียบก่อนและหลังการทดลอง",
    3: "สัตว์น ้ำในแม่น้ำกก",
}


def _one(field_id, value, sources):
    return {"answers": [{"field_id": field_id, "value": value, "source_blocks": sources}]}


def test_normalize_tolerates_pdf_tone_glitches():
    assert normalize_for_compare("สัตว์น ้ำ") == normalize_for_compare("สัตว์น้ำ")
    assert normalize_for_compare("นำ้") == normalize_for_compare("น้ำ")


def test_valid_text_answer_is_accepted():
    acc, rej = check_answers(_one("title_th", BLOCKS[0], [0]), T, BLOCKS)
    assert [a.field_id for a in acc] == ["title_th"] and rej == []


def test_valid_list_answer_is_accepted():
    acc, rej = check_answers(_one("objective_primary", [BLOCKS[1]], [1]), T, BLOCKS)
    assert len(acc) == 1 and rej == []


def test_user_field_is_rejected():
    acc, rej = check_answers(_one("pi_name", "x", [0]), T, BLOCKS)
    assert acc == [] and rej[0].code == "USER_FIELD"


def test_unknown_field_is_rejected():
    acc, rej = check_answers(_one("no_such_field", "x", [0]), T, BLOCKS)
    assert acc == [] and rej[0].code == "UNKNOWN_FIELD"


def test_text_not_in_source_is_rejected():
    acc, rej = check_answers(_one("title_th", "ข้อความที่แต่งขึ้นเอง", [0]), T, BLOCKS)
    assert acc == [] and rej[0].code == "NOT_IN_SOURCE"


def test_nonexistent_or_missing_block_is_rejected():
    _, rej = check_answers(_one("title_th", BLOCKS[0], [99]), T, BLOCKS)
    assert rej[0].code == "BAD_SOURCE"
    _, rej = check_answers(_one("title_th", BLOCKS[0], []), T, BLOCKS)
    assert rej[0].code == "BAD_SOURCE"


def test_wrong_shape_is_rejected():
    _, rej = check_answers(_one("objective_primary", BLOCKS[1], [1]), T, BLOCKS)
    assert rej[0].code == "BAD_SHAPE"


def test_unsupported_type_is_rejected():
    # ใช้ช่อง table จริงจากเทมเพลต
    table_id = next(f.id for f in T.iter_fields() if f.type.value == "table" and f.fill_by.value == "ai")
    _, rej = check_answers(_one(table_id, [["a"]], [0]), T, BLOCKS)
    assert rej[0].code in ("UNSUPPORTED_TYPE", "BAD_SHAPE")


def test_bad_response_shape():
    acc, rej = check_answers({"oops": 1}, T, BLOCKS)
    assert acc == [] and rej[0].code == "BAD_RESPONSE"


def test_unknown_mask_token_is_rejected_and_known_one_restored():
    r = Redactor()
    masked = r.redact("ติดต่อ a@b.com")
    blocks = {0: masked}
    _, rej = check_answers(_one("title_th", "{{EMAIL_9}}", [0]), T, blocks, r)
    assert rej[0].code == "UNKNOWN_TOKEN"
    acc, _ = check_answers(_one("title_th", masked, [0]), T, blocks, r)
    assert acc[0].value == "ติดต่อ a@b.com"


def test_apply_accepted_fills_form_and_tracks_source():
    acc, _ = check_answers(_one("title_th", BLOCKS[0], [0]), T, BLOCKS)
    form = FilledForm.blank(T, "th")
    apply_accepted(form, acc)
    v = form.values["title_th"]
    assert v.status == ValueStatus.FOUND and v.source_blocks == (0,)