"""
โครงข้อมูลกลางของ "คำตอบที่กรอกแล้ว" 1 ฉบับ (FilledForm)

form_fields.py บอกว่าฟอร์มมีช่องอะไรบ้าง ไฟล์นี้เก็บว่าแต่ละช่องตอนนี้มีค่าอะไร
และค่านั้นมาจากไหน เพื่อให้หน้าเว็บรู้ว่าช่องไหนต้องแสดงเป็นสีแดง

กติกาสำคัญจาก notes: ข้อมูลที่ผู้ใช้ต้องกรอกเอง AI ห้ามเติมให้
จึงบังคับไว้ในโค้ด (set_found จะ raise ถ้าช่องนั้น fill_by = user)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.form_fields import FieldDef, FieldType, FillBy, FormTemplate


class ValueStatus(str, Enum):
    FOUND = "found"                  # ระบบหาเจอจากไฟล์ที่อัปโหลด
    MISSING = "missing"              # ช่องของ AI ที่หาไม่เจอ -> สีแดง
    USER_REQUIRED = "user_required"  # ช่องของผู้ใช้ ยังไม่กรอก -> สีแดงเสมอ
    USER_FILLED = "user_filled"      # ผู้ใช้กรอกหรือแก้เองแล้ว
    AI_DRAFT = "ai_draft"            # AI สรุป/เรียบเรียงจากไฟล์ให้เป็นร่าง -> สีเหลือง ผู้ใช้ต้องตรวจทาน


# รูปแบบของ value ตามชนิดช่อง
#   text, textarea          -> str
#   numbered_list, bullet_list -> list[str]
#   table                   -> list[list[str]]   (แถว x คอลัมน์)
#   checkbox_group, checklist -> {"selected": [int, ...], "details": {"2": str}}
#   radio                   -> int   (ลำดับตัวเลือก เริ่มที่ 0)
#   yes_no                  -> bool


def is_blank(value: Any) -> bool:
    """ค่านี้ถือว่าว่างหรือไม่ (ไม่มีอะไรให้ผู้ใช้เห็นว่ากรอกแล้ว)"""
    if value is None:
        return True
    if isinstance(value, bool):          # False คือคำตอบ "ไม่ใช่" ไม่ใช่ค่าว่าง
        return False
    if isinstance(value, int):           # 0 คือตัวเลือกแรกของ radio
        return False
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, dict):
        return not value.get("selected") and not any(
            str(v).strip() for v in value.get("details", {}).values()
        )
    if isinstance(value, (list, tuple)):
        return all(is_blank(v) for v in value)
    return False


def check_value_shape(field: FieldDef, value: Any) -> None:
    """ตรวจว่ารูปแบบค่าตรงกับชนิดช่อง ถ้าไม่ตรงให้ raise ValueError"""
    if value is None:
        return
    t = field.type
    ok = True
    if t in (FieldType.TEXT, FieldType.TEXTAREA):
        ok = isinstance(value, str)
    elif t in (FieldType.NUMBERED_LIST, FieldType.BULLET_LIST):
        ok = isinstance(value, list) and all(isinstance(v, str) for v in value)
    elif t == FieldType.TABLE:
        ok = isinstance(value, list) and all(
            isinstance(r, list) and all(isinstance(c, str) for c in r) for r in value
        )
        if ok and field.columns:
            ok = all(len(r) == len(field.columns) for r in value)
    elif t in (FieldType.CHECKBOX_GROUP, FieldType.CHECKLIST):
        ok = (
            isinstance(value, dict)
            and isinstance(value.get("selected", []), list)
            and all(
                isinstance(i, int) and not isinstance(i, bool) and 0 <= i < len(field.options)
                for i in value.get("selected", [])
            )
            and isinstance(value.get("details", {}), dict)
        )
    elif t == FieldType.RADIO:
        ok = isinstance(value, int) and not isinstance(value, bool) and 0 <= value < len(field.options)
    elif t == FieldType.YES_NO:
        ok = isinstance(value, bool)
    if not ok:
        raise ValueError(f"ช่อง {field.id}: รูปแบบค่าไม่ตรงกับชนิด {t.value}")


@dataclass(frozen=True)
class FieldValue:
    """ค่าของ 1 ช่อง"""

    field_id: str
    status: ValueStatus
    value: Any = None
    source_blocks: tuple[int, ...] = ()   # Block.index ที่ระบบใช้เติมค่านี้ (ไว้ให้ผู้ใช้ตรวจย้อนกลับ)

    @property
    def is_red(self) -> bool:
        """ต้องแสดงเป็นสีแดงหรือไม่"""
        return self.status in (ValueStatus.MISSING, ValueStatus.USER_REQUIRED)


@dataclass
class FilledForm:
    template_id: str
    language: str
    values: dict[str, FieldValue]
    _template: FormTemplate

    # ---------- สร้างฟอร์มเปล่า ----------
    @classmethod
    def blank(cls, template: FormTemplate, language: str = "th") -> "FilledForm":
        """ทุกช่องเริ่มต้นเป็นสีแดง: ช่อง AI = MISSING, ช่องผู้ใช้ = USER_REQUIRED"""
        values = {
            f.id: FieldValue(
                f.id,
                ValueStatus.USER_REQUIRED if f.fill_by == FillBy.USER else ValueStatus.MISSING,
            )
            for f in template.iter_fields()
        }
        return cls(template.id, language, values, template)

    # ---------- เติมค่า ----------
    def set_found(self, field_id: str, value: Any, source_blocks: tuple[int, ...] = ()) -> None:
        """ให้ระบบ (AI/ตัวจับคู่) เติมค่า ทำได้เฉพาะช่อง fill_by = ai"""
        field = self._template.get_field(field_id)
        if field.fill_by == FillBy.USER:
            raise PermissionError(
                f"ช่อง {field_id} ผู้ใช้ต้องกรอกเอง ระบบห้ามเติมให้อัตโนมัติ"
            )
        check_value_shape(field, value)
        if is_blank(value):
            return   # หาไม่เจอ คงสถานะเดิม (MISSING) ไว้
        self.values[field_id] = FieldValue(field_id, ValueStatus.FOUND, value, tuple(source_blocks))

    def set_ai_draft(self, field_id: str, value: Any, source_blocks: tuple[int, ...] = ()) -> None:
        """AI เขียนร่างจากไฟล์ (สรุป/เรียบเรียงได้) ไม่ใช่ข้อความต้นฉบับ จึงแยกสถานะให้ผู้ใช้ตรวจทาน
        ห้ามช่องของผู้ใช้ เช่นเดียวกับ set_found"""
        field = self._template.get_field(field_id)
        if field.fill_by == FillBy.USER:
            raise PermissionError(
                f"ช่อง {field_id} ผู้ใช้ต้องกรอกเอง ระบบห้ามเติมให้อัตโนมัติ"
            )
        check_value_shape(field, value)
        if is_blank(value):
            return
        self.values[field_id] = FieldValue(field_id, ValueStatus.AI_DRAFT, value, tuple(source_blocks))

    def set_by_user(self, field_id: str, value: Any) -> None:
        """ผู้ใช้กรอก/แก้เอง ทำได้ทุกช่อง ถ้าล้างค่าจนว่างจะกลับเป็นสีแดง"""
        field = self._template.get_field(field_id)
        check_value_shape(field, value)
        if is_blank(value):
            status = ValueStatus.USER_REQUIRED if field.fill_by == FillBy.USER else ValueStatus.MISSING
            self.values[field_id] = FieldValue(field_id, status)
        else:
            self.values[field_id] = FieldValue(field_id, ValueStatus.USER_FILLED, value)

    # ---------- หมวดเสริม (gate) ----------
    def is_section_active(self, section_id: str) -> bool:
        """หมวดนี้ต้องแสดงหรือไม่ (gate ตอบ "ไม่ใช่" ที่หมวดนี้หรือหมวดแม่ = ตัดทิ้ง)"""
        for sec in self._template.section_chain(section_id):
            if sec.gate is not None and self.values[sec.gate.id].value is False:
                return False
        return True

    # ---------- สรุปผล ----------
    def red_fields(self) -> list[FieldDef]:
        """ช่องที่ต้องแสดงเป็นสีแดง เฉพาะหมวดที่ยังใช้งานอยู่ และไม่นับช่อง optional"""
        result = []
        for f in self._template.iter_fields():
            if not self.values[f.id].is_red or f.optional:
                continue
            if f.section_id and not self.is_section_active(f.section_id):
                continue
            result.append(f)
        return result

    def progress(self) -> dict[str, int]:
        """นับจำนวนช่องตามสถานะ (เฉพาะหมวดที่ยังใช้งานอยู่)"""
        counts = {s.value: 0 for s in ValueStatus}
        for f in self._template.iter_fields():
            if f.section_id and not self.is_section_active(f.section_id):
                continue
            counts[self.values[f.id].status.value] += 1
        return counts

    # ---------- แปลงเป็น dict (ส่งให้หน้าเว็บ / รับกลับมา) ----------
    def to_dict(self) -> dict:
        return {
            "template_id": self.template_id,
            "language": self.language,
            "values": {
                fid: {
                    "status": v.status.value,
                    "value": v.value,
                    "source_blocks": list(v.source_blocks),
                    "is_red": v.is_red,
                }
                for fid, v in self.values.items()
            },
        }

    @classmethod
    def from_dict(cls, template: FormTemplate, data: dict) -> "FilledForm":
        """สร้างจาก dict ที่หน้าเว็บส่งมา ตรวจรูปแบบและกฎ fill_by ซ้ำทุกช่อง (ไม่เชื่อข้อมูลจากฝั่งหน้าเว็บ)"""
        if data.get("template_id") != template.id:
            raise ValueError("template_id ไม่ตรงกับเทมเพลตที่เลือก")
        form = cls.blank(template, data.get("language", "th"))
        for fid, item in data.get("values", {}).items():
            template.get_field(fid)   # id แปลก -> KeyError
            status = ValueStatus(item["status"])
            value = item.get("value")
            if status == ValueStatus.FOUND:
                form.set_found(fid, value, tuple(item.get("source_blocks", ())))
            elif status == ValueStatus.AI_DRAFT:
                form.set_ai_draft(fid, value, tuple(item.get("source_blocks", ())))
            elif status == ValueStatus.USER_FILLED:
                form.set_by_user(fid, value)
        return form