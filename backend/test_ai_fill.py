"""ทดสอบขั้น 6 โดยไม่เรียก AI จริงและไม่ใช้เน็ต (ใช้ตัวปลอม)"""
import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.ai.client import AIError, AnthropicClient
from app.ai.fill import fill_form_from_blocks, parse_ai_json
from app.ai.prompts import build_user_prompt, fillable_fields
from app.filled_form import ValueStatus
from app.form_fields import FillBy, load_template

T = load_template(Path(__file__).resolve().parent / "ap02.json")
BLOCKS = [
    {"index": 0, "text": "ผลของการเดินเร็วต่อความดันโลหิต"},
    {"index": 1, "text": "ผู้วิจัยหลัก นางสาวสมหญิง ใจดี โทร 081-234-5678"},
    {"index": 2, "text": "เพื่อศึกษาผลของการเดินเร็ว"},
]


class FakeClient:
    def __init__(self, reply):
        self.reply, self.seen_user = reply, ""

    def complete(self, system, user):
        self.seen_user = user
        return self.reply


def test_prompt_only_lists_ai_fields_and_supported_types():
    ids = {f.id for f in fillable_fields(T)}
    assert "title_th" in ids and "pi_name" not in ids
    assert all(f.fill_by == FillBy.AI for f in fillable_fields(T))


def test_personal_data_never_reaches_ai_but_answer_is_restored():
    reply = json.dumps({"answers": [{"field_id": "title_th", "value": "ผลของการเดินเร็วต่อความดันโลหิต", "source_blocks": [0]}]})
    c = FakeClient(reply)
    res = fill_form_from_blocks(T, BLOCKS, c)
    assert "081-234-5678" not in c.seen_user and "สมหญิง" not in c.seen_user
    assert "{{PHONE_1}}" in c.seen_user
    assert res.form.values["title_th"].status == ValueStatus.FOUND
    assert res.redaction_summary.get("PHONE") == 1


def test_fabricated_answer_is_rejected_and_field_stays_red():
    reply = json.dumps({"answers": [{"field_id": "title_th", "value": "แต่งเอง", "source_blocks": [0]}]})
    res = fill_form_from_blocks(T, BLOCKS, FakeClient(reply))
    assert res.rejected[0].code == "NOT_IN_SOURCE"
    assert res.form.values["title_th"].is_red


def test_fenced_json_is_accepted_and_garbage_raises():
    assert parse_ai_json('```json\n{"answers": []}\n```') == {"answers": []}
    with pytest.raises(AIError) as e:
        parse_ai_json("ขออภัย ทำไม่ได้")
    assert e.value.code == "AI_BAD_RESPONSE"


def test_too_large_and_empty_input():
    with pytest.raises(AIError) as e:
        fill_form_from_blocks(T, BLOCKS, FakeClient("{}"), max_input_chars=10)
    assert e.value.code == "INPUT_TOO_LARGE"
    with pytest.raises(AIError) as e:
        fill_form_from_blocks(T, [{"index": 0, "text": "  "}], FakeClient("{}"))
    assert e.value.code == "NO_TEXT"


def _client(handler, key="k"):
    return AnthropicClient(key, "m", transport=httpx.MockTransport(handler))


def test_anthropic_client_success_and_errors():
    ok = _client(lambda r: httpx.Response(200, json={"content": [{"type": "text", "text": "hi"}]}))
    assert ok.complete("s", "u") == "hi"
    for status, code in ((401, "AI_AUTH"), (429, "AI_RATE_LIMIT"), (503, "AI_UNAVAILABLE")):
        with pytest.raises(AIError) as e:
            _client(lambda r, s=status: httpx.Response(s)).complete("s", "u")
        assert e.value.code == code

    def boom(request):
        raise httpx.ReadTimeout("t")
    with pytest.raises(AIError) as e:
        _client(boom).complete("s", "u")
    assert e.value.code == "AI_TIMEOUT"
    with pytest.raises(AIError) as e:
        _client(lambda r: httpx.Response(200), key="").complete("s", "u")
    assert e.value.code == "AI_NOT_CONFIGURED"
    assert "secret" not in repr(_client(lambda r: httpx.Response(200), key="secret-key"))


def test_fill_endpoint_with_fake_client(monkeypatch):
    from app.main import app
    from app.routers import analysis

    reply = json.dumps({"answers": [{"field_id": "title_th", "value": BLOCKS[0]["text"], "source_blocks": [0]}]})
    monkeypatch.setattr(analysis, "get_ai_client", lambda: FakeClient(reply))
    r = TestClient(app).post("/api/analysis/fill", json={"filename": "x.pdf", "blocks": BLOCKS, "mode": "extract"})
    assert r.status_code == 200
    body = r.json()
    assert body["form"]["values"]["title_th"]["status"] == "found"
    assert "081" not in json.dumps(body["redaction_summary"])
