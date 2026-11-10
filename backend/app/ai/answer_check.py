"""
ตรวจคำตอบที่ AI ส่งกลับมา "ก่อน" นำไปเติมในฟอร์ม (กติกา: AI ตอบได้เฉพาะข้อความที่มีในไฟล์)

AI ไม่ถูกเชื่อใจโดยอัตโนมัติ คำตอบแต่ละช่องต้องผ่านทุกข้อต่อไปนี้ ไม่ผ่านข้อใดก็ถูกปฏิเสธ
(ช่องนั้นจึงยังเป็นสีแดงให้ผู้ใช้กรอกเอง):
  1. ช่องต้องมีอยู่ในเทมเพลต และเป็นช่องที่ระบบเติมได้ (fill_by = ai) ห้ามแตะช่องของผู้ใช้
  2. ต้องอ้างเลข block ที่มีอยู่จริง
  3. ข้อความที่ตอบต้องปรากฏอยู่ใน block ที่อ้างจริง (ตรงตามต้นฉบับ ไม่ใช่เรียบเรียงใหม่)
  4. รูปแบบค่าต้องตรงกับชนิดช่อง
  5. ห้ามมีรหัสปิดบัง {{...}} ที่ระบบเราไม่ได้สร้าง

ขอบเขตตอนนี้: ช่องข้อความ (text, textarea) และรายการ (numbered_list, bullet_list) เท่านั้น
ช่องชนิดตาราง/ตัวเลือก/ใช่-ไม่ใช่ จะถูกปฏิเสธไว้ก่อนจนกว่าจะมีกติกาตรวจของตัวเอง

หมายเหตุ: block_texts ต้องเป็นข้อความชุดเดียวกับที่ส่งให้ AI (หลังปิดบังข้อมูลส่วนตัวแล้ว)
ฟังก์ชันนี้จะคืนค่าที่ใส่ข้อมูลจริงกลับให้แล้วผ่าน Redactor.restore
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from app.ai.redact import Redactor
from app.filled_form import FilledForm, check_value_shape, is_blank
from app.form_fields import FieldType, FillBy, FormTemplate

SUPPORTED_TYPES = (
    FieldType.TEXT,
    FieldType.TEXTAREA,
    FieldType.NUMBERED_LIST,
    FieldType.BULLET_LIST,
)
LIST_TYPES = (FieldType.NUMBERED_LIST, FieldType.BULLET_LIST)

# ---------- การทำให้ข้อความเทียบกันได้ (ใช้เทียบเท่านั้น ไม่แก้ข้อความจริง) ----------
# PDF ไทยมักอ่านออกมาเพี้ยน เช่น "น ้ำ" "นำ้" หรือไม้โทซ้ำ จึงปรับให้เป็นรูปมาตรฐานก่อนเทียบ
_TONE_MARKS = "\u0e48\u0e49\u0e4a\u0e4b"
_RE_SPACES = re.compile(r"\s+")
_RE_REPEATED_MARK = re.compile(r"([\u0e31\u0e34-\u0e3a\u0e47-\u0e4e])\1+")
_RE_SARA_AM_TONE = re.compile(f"\u0e33([{_TONE_MARKS}])")


def normalize_for_compare(text: str) -> str:
    s = unicodedata.normalize("NFC", text)
    s = s.replace("\u0e4d\u0e32", "\u0e33")          # นิคหิต + สระอา -> สระอำ
    s = _RE_SPACES.sub("", s)                        # ตัดช่องว่างทุกชนิด (รวมที่แทรกกลางคำ)
    s = _RE_REPEATED_MARK.sub(r"\1", s)              # สระ/วรรณยุกต์ซ้ำ -> ตัวเดียว
    s = _RE_SARA_AM_TONE.sub(lambda m: m.group(1) + "\u0e33", s)  # "นำ้" -> "น้ำ"
    s = s.replace("\u200b", "")                      # zero-width space
    return s.lower()


# ---------- ผลลัพธ์ ----------
@dataclass(frozen=True)
class Accepted:
    field_id: str
    value: Any                      # str หรือ list[str] (ใส่ข้อมูลจริงกลับแล้ว)
    source_blocks: tuple[int, ...]


@dataclass(frozen=True)
class Rejected:
    field_id: str | None            # None = คำตอบทั้งชุดใช้ไม่ได้
    code: str                       # ให้โปรแกรมใช้ เช่น "NOT_IN_SOURCE"
    message: str                    # อธิบายเหตุผล (ห้ามใส่เนื้อหาเอกสารลงข้อความนี้)


def _pieces(value: Any) -> list[str]:
    """แยกค่าเป็นชิ้นข้อความที่ต้องตรวจทีละชิ้น"""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [v for v in value if isinstance(v, str)]
    return []


def check_answers(
    raw: Any,
    template: FormTemplate,
    block_texts: dict[int, str],
    redactor: Redactor | None = None,
) -> tuple[list[Accepted], list[Rejected]]:
    """
    raw: ข้อมูลที่แปลงจาก JSON ของ AI แล้ว รูปแบบ
    {"answers": [{"field_id": "...", "value": ..., "source_blocks": [12, 13]}, ...]}
    block_texts: {เลข block: ข้อความที่ส่งให้ AI}
    คืนค่า (คำตอบที่รับได้, คำตอบที่ปฏิเสธพร้อมเหตุผล)
    """
    accepted: list[Accepted] = []
    rejected: list[Rejected] = []

    if not isinstance(raw, dict) or not isinstance(raw.get("answers"), list):
        return [], [Rejected(None, "BAD_RESPONSE", "คำตอบของ AI ไม่อยู่ในรูปแบบที่กำหนด")]

    seen: set[str] = set()
    normalized_blocks = {i: normalize_for_compare(t) for i, t in block_texts.items()}

    for item in raw["answers"]:
        if not isinstance(item, dict):
            rejected.append(Rejected(None, "BAD_ITEM", "รายการคำตอบไม่อยู่ในรูปแบบที่กำหนด"))
            continue

        field_id = item.get("field_id")
        if not isinstance(field_id, str):
            rejected.append(Rejected(None, "BAD_ITEM", "คำตอบไม่มี field_id"))
            continue

        # 1) ช่องต้องมีจริงและเป็นช่องที่ระบบเติมได้
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

        # 4) รูปแบบค่าต้องตรงกับชนิดช่อง
        try:
            check_value_shape(field, value)
        except ValueError:
            rejected.append(Rejected(field_id, "BAD_SHAPE", "รูปแบบค่าไม่ตรงกับชนิดช่อง"))
            continue
        if value is None or is_blank(value):
            rejected.append(Rejected(field_id, "EMPTY", "ไม่มีค่า (ถือว่าหาไม่พบ)"))
            continue

        # 2) ต้องอ้าง block ที่มีอยู่จริง
        sources = item.get("source_blocks")
        if (
            not isinstance(sources, list)
            or not sources
            or not all(isinstance(i, int) and not isinstance(i, bool) for i in sources)
        ):
            rejected.append(Rejected(field_id, "BAD_SOURCE", "ไม่ได้ระบุเลข block ที่มาของคำตอบ"))
            continue
        if any(i not in normalized_blocks for i in sources):
            rejected.append(Rejected(field_id, "BAD_SOURCE", "อ้างเลข block ที่ไม่มีอยู่จริง"))
            continue

        pieces = _pieces(value)

        # 5) ห้ามมีรหัสปิดบังที่เราไม่ได้สร้าง
        if redactor is not None and any(redactor.unknown_tokens(p) for p in pieces):
            rejected.append(Rejected(field_id, "UNKNOWN_TOKEN", "คำตอบมีรหัสปิดบังที่ระบบไม่ได้สร้าง"))
            continue

        # 3) ทุกชิ้นต้องปรากฏใน block ที่อ้างจริง
        haystack = "".join(normalized_blocks[i] for i in sources)
        if any(normalize_for_compare(p) not in haystack for p in pieces if p.strip()):
            rejected.append(Rejected(field_id, "NOT_IN_SOURCE", "ข้อความที่ตอบไม่ตรงกับข้อความใน block ที่อ้าง"))
            continue

        # ผ่านทั้งหมด: ใส่ข้อมูลจริงกลับ (ถ้ามีการปิดบัง)
        if redactor is not None:
            value = (
                redactor.restore(value)
                if isinstance(value, str)
                else [redactor.restore(p) for p in value]
            )
        seen.add(field_id)
        accepted.append(Accepted(field_id, value, tuple(sources)))

    return accepted, rejected


def apply_accepted(form: FilledForm, accepted: list[Accepted]) -> None:
    """เติมคำตอบที่ผ่านการตรวจแล้วลงฟอร์ม (set_found ห้ามช่องของผู้ใช้ซ้ำอีกชั้น)"""
    for a in accepted:
        form.set_found(a.field_id, a.value, a.source_blocks)