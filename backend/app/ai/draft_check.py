"""
ตัวตรวจ "ร่างจาก AI" (โหมดสรุป/เรียบเรียง) ต่างจาก answer_check.py ที่ต้องตรงต้นฉบับทุกตัวอักษร

โหมดนี้ AI สรุป ย่อ เรียบเรียง และปรับภาษาได้ จึงเทียบข้อความตรงๆ ไม่ได้
แต่ยังห้าม "แต่งข้อเท็จจริง" ด้วยการตรวจแบบเข้มเท่าที่ทำได้โดยไม่ต้องใช้ AI อีกตัว:
1. ช่องต้องมีอยู่ เป็นช่อง fill_by=ai ชนิดที่รองรับ ไม่ซ้ำ (เหมือน answer_check)
2. รูปแบบค่าตรงชนิดช่อง ไม่ว่าง
3. ต้องอ้างบล็อกที่ "ส่งให้ AI จริง"
4. ห้ามมีรหัสปิดบัง {{...}} ที่ระบบไม่ได้สร้าง
5. ตัวเลขทุกตัว (2 หลักขึ้นไป หรือมีทศนิยม) ในร่าง ต้องมีในบล็อกที่อ้าง
(กันสถิติ จำนวนคน ปี งบประมาณ ที่ AI แต่งขึ้นเอง ไม่ว่าจะเขียนเลขไทยหรืออารบิก)
6. เนื้อหาต้องสอดคล้องกับบล็อกที่อ้าง: ชุดตัวอักษร 4 ตัวติดกันของร่างต้องพบในบล็อกอย่างน้อย
MIN_OVERLAP (กันการอ้างบล็อกผิดหรือเขียนเรื่องที่ไม่เกี่ยวกับไฟล์)

ข้อจำกัด (ต้องบอกผู้ใช้ตามจริง): ตัวตรวจนี้จับการแต่งตัวเลข และการอ้างผิดบล็อกแบบชัดเจนได้
แต่จับข้อเท็จจริงที่ไม่ใช่ตัวเลข เช่น เหตุผลหรือข้อสรุปที่ AI เพิ่มเอง ไม่ได้
จึงต้องให้ผู้ใช้ตรวจทานทุกช่องที่เป็นสีเหลือง ค่า MIN_OVERLAP ควรปรับตามผลทดสอบกับไฟล์จริง
"""

from __future__ import annotations

import re
from typing import Any

from app.ai.answer_check import (
    SUPPORTED_TYPES,
    Accepted,
    Rejected,
    _pieces,
    normalize_for_compare,
)
from app.ai.redact import Redactor
from app.filled_form import check_value_shape, is_blank
from app.form_fields import FillBy, FormTemplate

MIN_OVERLAP = 0.25
MAX_SOURCES = 40
_NGRAM = 4

_THAI_DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
_RE_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
_RE_TOKEN = re.compile(r"\{\{[A-Z_]+_\d+\}\}")


def numbers_in(text: str) -> set[str]:
    """ตัวเลขที่ต้องตรวจ: 2 หลักขึ้นไป หรือมีทศนิยม (ตัดจุลภาคออก) เลขไทยแปลงเป็นอารบิก
    ไม่นับรหัสปิดบัง เช่น {{PHONE_1}} เพราะเป็นรหัสที่ระบบสร้าง"""
    t = _RE_TOKEN.sub(" ", text).translate(_THAI_DIGITS)
    out = set()
    for m in _RE_NUMBER.findall(t):
        n = m.replace(",", "").rstrip(".")
        if "." in n or len(n) >= 2:
            out.add(n)
    return out


def _grams(norm: str) -> set[str]:
    return {norm[i : i + _NGRAM] for i in range(len(norm) - _NGRAM + 1)}


def overlap_ratio(answer: str, source: str) -> float:
    a, s = normalize_for_compare(answer), normalize_for_compare(source)
    if len(a) < _NGRAM:
        return 1.0 if a and a in s else 0.0
    ga = _grams(a)
    return len(ga & _grams(s)) / len(ga) if ga else 0.0


def check_drafts(
    raw: Any,
    template: FormTemplate,
    block_texts: dict[int, str],
    redactor: Redactor | None = None,
    min_overlap: float = MIN_OVERLAP,
) -> tuple[list[Accepted], list[Rejected]]:
    """รูปแบบ raw และผลลัพธ์เหมือน check_answers ทุกประการ (แทนที่กันได้)"""
    accepted: list[Accepted] = []
    rejected: list[Rejected] = []

    if not isinstance(raw, dict) or not isinstance(raw.get("answers"), list):
        return [], [Rejected(None, "BAD_RESPONSE", "คำตอบของ AI ไม่อยู่ในรูปแบบที่กำหนด")]

    seen: set[str] = set()
    for item in raw["answers"]:
        if not isinstance(item, dict) or not isinstance(item.get("field_id"), str):
            rejected.append(Rejected(None, "BAD_ITEM", "รายการคำตอบไม่อยู่ในรูปแบบที่กำหนด"))
            continue
        field_id = item["field_id"]

        try:
            field = template.get_field(field_id)
        except KeyError:
            rejected.append(Rejected(field_id, "UNKNOWN_FIELD", "ไม่มีช่องนี้ในเทมเพลต"))
            continue
        if field.fill_by != FillBy.AI:
            rejected.append(Rejected(field_id, "USER_FIELD", "ช่องนี้ผู้ใช้ต้องกรอกเอง ระบบห้ามเติมให้"))
            continue
        if field.type not in SUPPORTED_TYPES:
            rejected.append(Rejected(field_id, "UNSUPPORTED_TYPE", "ชนิดช่องนี้ยังไม่รองรับการเติมอัตโนมัติ"))
            continue
        if field_id in seen:
            rejected.append(Rejected(field_id, "DUPLICATE", "มีคำตอบซ้ำสำหรับช่องเดียวกัน (ใช้ตัวแรก)"))
            continue

        value = item.get("value")
        try:
            check_value_shape(field, value)
        except ValueError:
            rejected.append(Rejected(field_id, "BAD_SHAPE", "รูปแบบค่าไม่ตรงกับชนิดช่อง"))
            continue
        if value is None or is_blank(value):
            rejected.append(Rejected(field_id, "EMPTY", "ไม่มีค่า (ถือว่าหาไม่พบ)"))
            continue

        sources = item.get("source_blocks")
        if (
            not isinstance(sources, list)
            or not sources
            or len(sources) > MAX_SOURCES
            or not all(isinstance(i, int) and not isinstance(i, bool) for i in sources)
        ):
            rejected.append(Rejected(field_id, "BAD_SOURCE", "ไม่ได้ระบุเลข block ที่มาของคำตอบ"))
            continue
        if any(i not in block_texts for i in sources):
            rejected.append(Rejected(field_id, "BAD_SOURCE", "อ้างเลข block ที่ไม่มีอยู่จริง"))
            continue

        pieces = [p for p in _pieces(value) if p.strip()]
        joined = "\n".join(pieces)

        if redactor is not None and redactor.unknown_tokens(joined):
            rejected.append(Rejected(field_id, "UNKNOWN_TOKEN", "คำตอบมีรหัสปิดบังที่ระบบไม่ได้สร้าง"))
            continue

        source_text = "\n".join(block_texts[i] for i in sources)
        if not numbers_in(joined) <= numbers_in(source_text):
            rejected.append(Rejected(field_id, "NUMBER_NOT_IN_SOURCE", "มีตัวเลขที่ไม่ปรากฏใน block ที่อ้าง"))
            continue
        if overlap_ratio(joined, source_text) < min_overlap:
            rejected.append(Rejected(field_id, "LOW_OVERLAP", "เนื้อหาไม่สอดคล้องกับ block ที่อ้าง"))
            continue

        if redactor is not None:
            value = (
                redactor.restore(value)
                if isinstance(value, str)
                else [redactor.restore(p) for p in value]
            )
        seen.add(field_id)
        accepted.append(Accepted(field_id, value, tuple(sources)))

    return accepted, rejected


def apply_drafts(form, accepted: list[Accepted]) -> None:
    """เติมร่างที่ผ่านการตรวจแล้วลงฟอร์มด้วยสถานะ AI_DRAFT (สีเหลือง ให้ผู้ใช้ตรวจทาน)"""
    for a in accepted:
        form.set_ai_draft(a.field_id, a.value, a.source_blocks)
