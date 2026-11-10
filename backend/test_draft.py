"""ทดสอบโหมด "ร่างจาก AI" (draft_check.py, pipeline.py, endpoint) ไม่เรียก AI จริง ไม่ใช้เน็ต"""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.ai.client import AIError
from app.ai.draft_check import check_drafts, numbers_in, overlap_ratio
from app.ai.pipeline import draft_form_from_blocks, select_context, split_chunks
from app.ai.prompts import draftable_fields
from app.ai.redact import Redactor
from app.filled_form import FilledForm, ValueStatus
from app.form_fields import load_template

T = load_template(Path(__file__).resolve().parent / "ap02.json")

SRC = {
    0: "การวิจัยครั้งนี้มีวัตถุประสงค์เพื่อศึกษาผลของโปรแกรมเดินเร็วต่อความดันโลหิตของผู้สูงอายุ",
    1: "กลุ่มตัวอย่างคือผู้สูงอายุจำนวน ๑๒๐ คน ในอำเภอแม่ลาว จังหวัดเชียงราย",
    2: "ตลาดหุ้นไทยปิดบวก 15 จุดเมื่อวาน",
}


def _ans(fid, value, blocks):
    return {"answers": [{"field_id": fid, "value": value, "source_blocks": blocks}]}


# ---------- ตัวตรวจ ----------
def test_numbers_and_overlap_helpers():
    assert numbers_in("ผู้สูงอายุ ๑๒๐ คน งบ 150,000 บาท ข้อ 3") == {"120", "150000"}
    assert overlap_ratio("ศึกษาผลของโปรแกรมเดินเร็ว", SRC[0]) > 0.8
    assert overlap_ratio("ตลาดหุ้นผันผวนมาก", SRC[0]) < 0.1


def test_paraphrase_with_thai_digits_in_source_is_accepted():
    raw = _ans("sample_size", "ผู้สูงอายุ 120 คน ในอำเภอแม่ลาว จังหวัดเชียงราย", [1])
    acc, rej = check_drafts(raw, T, SRC)
    assert len(acc) == 1 and rej == []


def test_invented_number_is_rejected():
    raw = _ans("sample_size", "ผู้สูงอายุจำนวน 150 คน ในอำเภอแม่ลาว", [1])
    _, rej = check_drafts(raw, T, SRC)
    assert rej[0].code == "NUMBER_NOT_IN_SOURCE"


def test_unrelated_text_or_wrong_citation_is_rejected():
    raw = _ans("background", "บริษัทจดทะเบียนมีผลประกอบการดีขึ้นอย่างต่อเนื่อง", [0])
    _, rej = check_drafts(raw, T, SRC)
    assert rej[0].code == "LOW_OVERLAP"


def test_user_field_unknown_field_bad_source_unknown_token():
    assert check_drafts(_ans("pi_name", "x", [0]), T, SRC)[1][0].code == "USER_FIELD"
    assert check_drafts(_ans("nope", "x", [0]), T, SRC)[1][0].code == "UNKNOWN_FIELD"
    assert check_drafts(_ans("background", SRC[0], [77]), T, SRC)[1][0].code == "BAD_SOURCE"
    assert check_drafts(_ans("background", SRC[0], []), T, SRC)[1][0].code == "BAD_SOURCE"
    r = Redactor(); r.redact("a@b.com")
    assert check_drafts(_ans("background", SRC[0] + " {{EMAIL_9}}", [0]), T, SRC, r)[1][0].code == "UNKNOWN_TOKEN"


def test_list_draft_accepted_and_masked_values_restored():
    r = Redactor()
    masked = {0: r.redact("ติดต่อผู้วิจัยทางอีเมล a@b.com เพื่อสอบถามผลของโปรแกรมเดินเร็ว")}
    raw = _ans("objective_primary", ["ผลของโปรแกรมเดินเร็ว ติดต่อ {{EMAIL_1}}"], [0])
    acc, rej = check_drafts(raw, T, masked, r)
    assert rej == [] and acc[0].value == ["ผลของโปรแกรมเดินเร็ว ติดต่อ a@b.com"]


# ---------- สถานะ AI_DRAFT ในฟอร์ม ----------
def test_ai_draft_status_rules_and_roundtrip():
    form = FilledForm.blank(T, "th")
    form.set_ai_draft("background", "ร่างความสำคัญ", (0,))
    v = form.values["background"]
    assert v.status == ValueStatus.AI_DRAFT and not v.is_red
    with pytest.raises(PermissionError):
        form.set_ai_draft("pi_name", "x")
    again = FilledForm.from_dict(T, form.to_dict())
    assert again.values["background"].status == ValueStatus.AI_DRAFT
    assert again.values["background"].source_blocks == (0,)


def test_special_category_fields_are_not_requested():
    ids = {f.id for f in draftable_fields(T)}
    assert "background" in ids and "objective_primary" in ids
    assert not ids & {"food_1", "supp_1", "herb_2", "cos_2"}


# ---------- สายงานทั้งหมด ----------
class RoutingFake:
    """ตอบตามชนิดคำสั่ง: ค้นหา (locate) หรือ ร่าง (draft)"""
    def __init__(self, locate=None, draft=None):
        self.locate, self.draft = locate or {}, draft
        self.locate_calls = self.draft_calls = 0
        self.draft_user = ""

    def complete(self, system, user):
        if "ค้นหา" in system:
            self.locate_calls += 1
            return json.dumps({"locate": [{"field_id": f, "blocks": b} for f, b in self.locate.items()]})
        self.draft_calls += 1
        self.draft_user = user
        return json.dumps(self.draft)


BLOCKS = [{"index": i, "text": t} for i, t in SRC.items()]


def test_short_document_single_call_and_masking():
    blocks = BLOCKS + [{"index": 3, "text": "ผู้วิจัย นางสาวสมหญิง ใจดี โทร 081-234-5678"}]
    draft = _ans("sample_size", "ผู้สูงอายุ 120 คน ในอำเภอแม่ลาว", [1])
    c = RoutingFake(draft=draft)
    res = draft_form_from_blocks(T, blocks, c)
    assert c.locate_calls == 0 and c.draft_calls == 1
    assert "081-234-5678" not in c.draft_user and "สมหญิง" not in c.draft_user
    assert res.form.values["sample_size"].status == ValueStatus.AI_DRAFT
    assert res.redaction_summary.get("PHONE") == 1


def test_long_document_locates_then_drafts_only_relevant_blocks():
    c = RoutingFake(
        locate={"sample_size": [1], "background": [0]},
        draft=_ans("sample_size", "ผู้สูงอายุ 120 คน", [1]),
    )
    res = draft_form_from_blocks(T, BLOCKS, c, max_input_chars=170, chunk_chars=100)
    assert c.locate_calls == res.stats["chunks"] >= 2 and c.draft_calls == 1
    assert "[B2]" not in c.draft_user and "ตลาดหุ้น" not in c.draft_user     # บล็อกที่ไม่เกี่ยวไม่ถูกส่ง
    assert res.form.values["sample_size"].status == ValueStatus.AI_DRAFT


def test_nothing_located_and_errors():
    res = draft_form_from_blocks(T, BLOCKS, RoutingFake(locate={}), max_input_chars=150, chunk_chars=100)
    assert res.rejected[0].code == "NOTHING_LOCATED"
    with pytest.raises(AIError) as e:
        draft_form_from_blocks(T, BLOCKS, RoutingFake(), max_input_chars=10, chunk_chars=10, max_chunks=1)
    assert e.value.code == "INPUT_TOO_LARGE"
    with pytest.raises(AIError) as e:
        draft_form_from_blocks(T, [{"index": 0, "text": " "}], RoutingFake())
    assert e.value.code == "NO_TEXT"


def test_helpers_chunking_and_budget():
    ch = split_chunks({0: "aaaa", 1: "bbbb", 2: "cc"}, 6)
    assert [list(c) for c in ch] == [[0], [1, 2]]
    ctx = select_context({"f1": [0, 1], "f2": [2]}, {0: "x" * 5, 1: "y" * 5, 2: "z" * 5}, 10)
    assert set(ctx) == {0, 2}          # แบ่งโควตาให้ทุกช่องก่อน


def test_endpoint_draft_mode(monkeypatch):
    from app.main import app
    from app.routers import analysis

    fake = RoutingFake(draft=_ans("sample_size", "ผู้สูงอายุ 120 คน ในอำเภอแม่ลาว", [1]))
    monkeypatch.setattr(analysis, "get_ai_client", lambda: fake)
    r = TestClient(app).post("/api/analysis/fill", json={"filename": "x.pdf", "blocks": BLOCKS})
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "draft" and body["form"]["values"]["sample_size"]["status"] == "ai_draft"
    bad = TestClient(app).post("/api/analysis/fill", json={"filename": "x", "blocks": BLOCKS, "mode": "zzz"})
    assert bad.status_code == 422
