"""
ตัวประสานงานขั้น 6: เอกสารที่อ่านแล้ว -> ปิดบังข้อมูลส่วนตัว -> ถาม AI -> ตรวจคำตอบ -> เติมฟอร์ม

ลำดับ (แต่ละขั้นมีไฟล์รับผิดชอบของตัวเอง):
redact.py       ปิดบังอีเมล/เบอร์/เลขบัตร/ชื่อมีคำนำหน้า ก่อนส่งออกนอกเครื่อง
prompts.py      ประกอบข้อความสั่ง
client.py       เรียก AI
answer_check.py ตรวจคำตอบทีละช่อง (ไม่ผ่าน = ช่องยังแดง)
คืน FilledForm + รายการที่ถูกปฏิเสธ (ให้หน้าเว็บอธิบายผู้ใช้ได้)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from app.ai.answer_check import Accepted, Rejected, apply_accepted, check_answers
from app.ai.client import AIClient, AIError
from app.ai.prompts import SYSTEM_PROMPT, build_user_prompt
from app.ai.redact import Redactor
from app.filled_form import FilledForm
from app.form_fields import FormTemplate


@dataclass
class FillResult:
    form: FilledForm
    accepted: list[Accepted]
    rejected: list[Rejected]
    redaction_summary: dict[str, int] = field(default_factory=dict)   # จำนวนที่ปิดบัง (ไม่มีค่าจริง)


def parse_ai_json(text: str) -> Any:
    """แปลงคำตอบ AI เป็น JSON (ทนต่อกรณี AI ใส่ ``` หรือมีข้อความนำหน้า/ตามหลัง)"""
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    start, end = s.find("{"), s.rfind("}")
    if start == -1 or end <= start:
        raise AIError("AI_BAD_RESPONSE", "คำตอบจาก AI ไม่อยู่ในรูปแบบ JSON", 502)
    try:
        return json.loads(s[start : end + 1])
    except json.JSONDecodeError:
        raise AIError("AI_BAD_RESPONSE", "คำตอบจาก AI ไม่อยู่ในรูปแบบ JSON", 502) from None


def fill_form_from_blocks(
    template: FormTemplate,
    blocks: Iterable[dict],
    client: AIClient,
    *,
    language: str = "th",
    max_input_chars: int = 60000,
) -> FillResult:
    """blocks: [{"index": int, "text": str}, ...] (รูปแบบเดียวกับที่ /upload คืน)"""
    redactor = Redactor()          # 1 งาน 1 ตัว: ตารางจับคู่อยู่ในหน่วยความจำ ไม่เขียนไฟล์
    block_texts: dict[int, str] = {}
    for b in blocks:
        idx, text = b.get("index"), b.get("text")
        if isinstance(idx, int) and not isinstance(idx, bool) and isinstance(text, str) and text.strip():
            block_texts[idx] = redactor.redact(text)     # ใช้ชุดที่ปิดบังแล้วชุดเดียวทั้งส่งและตรวจ

    if not block_texts:
        raise AIError("NO_TEXT", "ไม่มีข้อความให้ AI วิเคราะห์", 422)
    if sum(len(t) for t in block_texts.values()) > max_input_chars:
        raise AIError(
            "INPUT_TOO_LARGE",
            "เอกสารยาวเกินกว่าที่ระบบส่งให้ AI ได้ในครั้งเดียว (ยังไม่รองรับการแบ่งส่ง)",
            413,
        )

    raw_text = client.complete(SYSTEM_PROMPT, build_user_prompt(template, block_texts))
    accepted, rejected = check_answers(parse_ai_json(raw_text), template, block_texts, redactor)

    form = FilledForm.blank(template, language)
    apply_accepted(form, accepted)
    return FillResult(form, accepted, rejected, redactor.summary())
