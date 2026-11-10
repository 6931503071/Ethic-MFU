"""
โครงข้อมูลกลางของ "ช่องในเทมเพลต" (templates/*.json)

อ่านไฟล์เทมเพลตแล้วแปลงเป็นวัตถุที่โปรแกรมใช้ต่อได้ โดยไม่ต้องไปแตะ dict ดิบ ๆ ทั่วโปรแกรม
ไฟล์นี้อธิบายแค่ "หน้าตาของฟอร์ม" ส่วน "คำตอบที่กรอกแล้ว" อยู่ใน filled_form.py
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterator


class FieldType(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    TABLE = "table"
    NUMBERED_LIST = "numbered_list"
    BULLET_LIST = "bullet_list"
    CHECKBOX_GROUP = "checkbox_group"
    RADIO = "radio"
    CHECKLIST = "checklist"
    YES_NO = "yes_no"


class FillBy(str, Enum):
    AI = "ai"      # ระบบเติมจากไฟล์ที่อัปโหลด ถ้าไม่พบให้เป็นช่องสีแดง
    USER = "user"  # ผู้ใช้กรอกเอง แดงเสมอ (ข้อมูลส่วนตัว วันที่ ตัวเลขเงิน)


class TemplateError(Exception):
    """เทมเพลตมีรูปแบบไม่ถูกต้อง ข้อความระบุ id ของจุดที่ผิดไว้ให้แล้ว"""


@dataclass(frozen=True)
class FieldDef:
    """ช่อง 1 ช่องในฟอร์ม (รวมช่องคำถาม gate และช่องในหัวกระดาษ)"""

    id: str
    type: FieldType
    fill_by: FillBy
    label: str = ""
    label_en: str = ""
    hint: str = ""
    hint_en: str = ""
    optional: bool = False
    attach_separately: bool = False
    with_detail: bool = False
    min_rows: int = 0
    min_items: int = 0
    columns: tuple[str, ...] = ()
    columns_en: tuple[str, ...] = ()
    options: tuple[str, ...] = ()
    options_en: tuple[str, ...] = ()
    row_options: tuple[str, ...] = ()
    row_options_en: tuple[str, ...] = ()
    rows: tuple[str, ...] = ()
    rows_en: tuple[str, ...] = ()
    red_columns: tuple[int, ...] = ()
    yes_label: str = ""
    no_label: str = ""
    yes_label_en: str = ""
    no_label_en: str = ""
    section_id: str = ""      # ช่องนี้อยู่ในหมวดไหน ("" = หัวกระดาษ)
    is_gate: bool = False     # เป็นคำถามใช่/ไม่ใช่ของหมวดเสริมหรือไม่
    is_header: bool = False   # เป็นช่องหัวกระดาษ (Version, Date) หรือไม่

    def text(self, lang: str = "th") -> str:
        """ชื่อช่องตามภาษา ถ้าไม่มีคำแปลให้ใช้ภาษาไทย"""
        return self.label_en if lang == "en" and self.label_en else self.label

    def hint_text(self, lang: str = "th") -> str:
        return self.hint_en if lang == "en" and self.hint_en else self.hint

    def option_list(self, lang: str = "th") -> tuple[str, ...]:
        return self.options_en if lang == "en" and self.options_en else self.options


@dataclass(frozen=True)
class SectionDef:
    id: str
    number: str                 # เป็น str เพราะมีค่าอย่าง "3.1" และ "A"
    title: str
    title_en: str = ""
    hint: str = ""
    hint_en: str = ""
    optional: bool = False
    gate: FieldDef | None = None
    fields: tuple[FieldDef, ...] = ()
    subsections: tuple["SectionDef", ...] = ()
    parent_id: str = ""

    def text(self, lang: str = "th") -> str:
        return self.title_en if lang == "en" and self.title_en else self.title


@dataclass(frozen=True)
class FormTemplate:
    id: str
    form_code: str
    name: str
    name_en: str
    languages: tuple[str, ...]
    header_fields: tuple[FieldDef, ...]
    sections: tuple[SectionDef, ...]
    format: dict        # ค่าจัดหน้า (A4, ขอบ, ฟอนต์) เก็บดิบไว้ก่อน
    footer: dict
    rules: dict
    warnings: tuple[str, ...] = ()   # คีย์แปลกที่ไม่รู้จัก (ไม่ใช่ error แต่ควรรู้)

    # ---------- ตัวช่วยค้นหา ----------
    def iter_sections(self) -> Iterator[SectionDef]:
        def walk(items):
            for s in items:
                yield s
                yield from walk(s.subsections)
        yield from walk(self.sections)

    def iter_fields(self, include_header: bool = True) -> Iterator[FieldDef]:
        """วนทุกช่องตามลำดับในฟอร์ม รวม gate (gate มาก่อนช่องของหมวดนั้น)"""
        if include_header:
            yield from self.header_fields
        for s in self.iter_sections():
            if s.gate is not None:
                yield s.gate
            yield from s.fields

    def get_field(self, field_id: str) -> FieldDef:
        for f in self.iter_fields():
            if f.id == field_id:
                return f
        raise KeyError(f"ไม่พบช่อง id={field_id!r} ในเทมเพลต {self.id}")

    def get_section(self, section_id: str) -> SectionDef:
        for s in self.iter_sections():
            if s.id == section_id:
                return s
        raise KeyError(f"ไม่พบหมวด id={section_id!r} ในเทมเพลต {self.id}")

    def section_chain(self, section_id: str) -> list[SectionDef]:
        """หมวดนี้ + หมวดแม่ทั้งหมด (จากในสุดไปนอกสุด)"""
        chain = []
        current = section_id
        while current:
            s = self.get_section(current)
            chain.append(s)
            current = s.parent_id
        return chain

    def fields_by(self, fill_by: FillBy) -> list[FieldDef]:
        return [f for f in self.iter_fields() if f.fill_by == fill_by]


# ---------------------------------------------------------------- ตัวโหลด

_FIELD_KEYS = {
    "id", "type", "fill_by", "label", "label_en", "hint", "hint_en", "optional",
    "attach_separately", "with_detail", "min_rows", "min_items", "columns",
    "columns_en", "options", "options_en", "row_options", "row_options_en",
    "rows", "rows_en", "red_columns", "red_columns_note",
}
_GATE_KEYS = {"id", "type", "fill_by", "yes_label", "no_label", "yes_label_en", "no_label_en"}
_SECTION_KEYS = {"id", "number", "title", "title_en", "hint", "hint_en", "optional", "gate", "fields", "subsections"}


def _enum(enum_cls, value, where: str):
    try:
        return enum_cls(value)
    except ValueError:
        valid = ", ".join(e.value for e in enum_cls)
        raise TemplateError(f"{where}: ค่า {value!r} ไม่ถูกต้อง (ที่รองรับ: {valid})") from None


def _warn_unknown(raw: dict, known: set, where: str, warnings: list[str]) -> None:
    for key in raw:
        if key not in known:
            warnings.append(f"{where}: ไม่รู้จักคีย์ {key!r}")


def _parse_field(raw: dict, section_id: str, warnings: list[str]) -> FieldDef:
    fid = raw.get("id")
    if not fid:
        raise TemplateError(f"หมวด {section_id or 'header'}: มีช่องที่ไม่มี id")
    _warn_unknown(raw, _FIELD_KEYS, f"ช่อง {fid}", warnings)
    t = _enum(FieldType, raw.get("type", "text"), f"ช่อง {fid} (type)")
    fb = _enum(FillBy, raw.get("fill_by", "user"), f"ช่อง {fid} (fill_by)")

    def tup(key):
        return tuple(raw.get(key, ()))

    return FieldDef(
        id=fid, type=t, fill_by=fb,
        label=raw.get("label", ""), label_en=raw.get("label_en", ""),
        hint=raw.get("hint", ""), hint_en=raw.get("hint_en", ""),
        optional=raw.get("optional", False),
        attach_separately=raw.get("attach_separately", False),
        with_detail=raw.get("with_detail", False),
        min_rows=raw.get("min_rows", 0), min_items=raw.get("min_items", 0),
        columns=tup("columns"), columns_en=tup("columns_en"),
        options=tup("options"), options_en=tup("options_en"),
        row_options=tup("row_options"), row_options_en=tup("row_options_en"),
        rows=tup("rows"), rows_en=tup("rows_en"),
        red_columns=tup("red_columns"),
        section_id=section_id,
    )


def _parse_gate(raw: dict, section: dict, warnings: list[str]) -> FieldDef:
    gid = raw.get("id")
    if not gid:
        raise TemplateError(f"หมวด {section['id']}: gate ไม่มี id")
    _warn_unknown(raw, _GATE_KEYS, f"gate {gid}", warnings)
    return FieldDef(
        id=gid, type=FieldType.YES_NO,
        fill_by=_enum(FillBy, raw.get("fill_by", "ai"), f"gate {gid} (fill_by)"),
        label=section.get("title", ""), label_en=section.get("title_en", ""),
        yes_label=raw.get("yes_label", ""), no_label=raw.get("no_label", ""),
        yes_label_en=raw.get("yes_label_en", ""), no_label_en=raw.get("no_label_en", ""),
        section_id=section["id"], is_gate=True,
    )


def _parse_section(raw: dict, parent_id: str, warnings: list[str]) -> SectionDef:
    sid = raw.get("id")
    if not sid:
        raise TemplateError("มีหมวดที่ไม่มี id")
    _warn_unknown(raw, _SECTION_KEYS, f"หมวด {sid}", warnings)
    return SectionDef(
        id=sid,
        number=str(raw.get("number", "")),
        title=raw.get("title", ""),
        title_en=raw.get("title_en", ""),
        hint=raw.get("hint", ""),
        hint_en=raw.get("hint_en", ""),
        optional=raw.get("optional", False),
        gate=_parse_gate(raw["gate"], raw, warnings) if raw.get("gate") else None,
        fields=tuple(_parse_field(f, sid, warnings) for f in raw.get("fields", ())),
        subsections=tuple(_parse_section(s, sid, warnings) for s in raw.get("subsections", ())),
        parent_id=parent_id,
    )


def validate_template(t: FormTemplate) -> list[str]:
    """คืนรายการปัญหา (ว่าง = ผ่าน)"""
    problems: list[str] = []
    seen: set[str] = set()
    for f in t.iter_fields():
        if f.id in seen:
            problems.append(f"id ซ้ำ: {f.id}")
        seen.add(f.id)
        if f.type == FieldType.TABLE and not f.columns:
            problems.append(f"ช่อง {f.id}: table ต้องมี columns")
        if f.type in (FieldType.CHECKBOX_GROUP, FieldType.RADIO, FieldType.CHECKLIST) and not f.options:
            problems.append(f"ช่อง {f.id}: {f.type.value} ต้องมี options")
        for th, en, name in (
            (f.options, f.options_en, "options"),
            (f.columns, f.columns_en, "columns"),
            (f.row_options, f.row_options_en, "row_options"),
            (f.rows, f.rows_en, "rows"),
        ):
            if en and len(th) != len(en):
                problems.append(f"ช่อง {f.id}: {name} ไทย {len(th)} ข้อ แต่อังกฤษ {len(en)} ข้อ")
    return problems


def load_template(path: Path | str, *, strict: bool = True) -> FormTemplate:
    """อ่านเทมเพลต JSON แล้วคืน FormTemplate

    strict=True: ถ้า validate_template เจอปัญหา จะ raise TemplateError ทันที
    """
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TemplateError(f"อ่านเทมเพลต {path} ไม่ได้: {exc}") from exc

    warnings: list[str] = []
    header_fields = tuple(
        FieldDef(
            id=h["id"], type=FieldType.TEXT,
            fill_by=_enum(FillBy, h.get("fill_by", "user"), f"header {h['id']} (fill_by)"),
            label=h.get("label", ""), is_header=True,
        )
        for h in raw.get("header", {}).get("fields", ())
    )
    template = FormTemplate(
        id=raw["id"],
        form_code=raw.get("form_code", ""),
        name=raw.get("name", ""),
        name_en=raw.get("name_en", ""),
        languages=tuple(raw.get("languages_available", ("th",))),
        header_fields=header_fields,
        sections=tuple(_parse_section(s, "", warnings) for s in raw.get("sections", ())),
        format=raw.get("format", {}),
        footer=raw.get("footer", {}),
        rules=raw.get("rules", {}),
        warnings=tuple(warnings),
    )
    problems = validate_template(template)
    if problems and strict:
        raise TemplateError("เทมเพลตมีปัญหา:\n- " + "\n- ".join(problems))
    return template