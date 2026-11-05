# backend/app/suspects.py
"""
ตัวตรวจ "จุดสงสัย" (suspects) แบบกฎตายตัว (rule-based) ไม่ใช้ AI

หลักการสำคัญ:
  1) ไม่แก้ข้อความต้นฉบับเด็ดขาด ตัวตรวจแค่ "ปักธง" พร้อมเหตุผลและข้อเสนอ (ถ้ามั่นใจ)
  2) ถ้าไม่แน่ใจจริง ๆ จะไม่ใส่ข้อเสนอแก้ (suggestion = None) ให้ผู้ใช้ตัดสินใจเอง
  3) สีตามที่โปรเจกต์กำหนด: red = ต้องแก้/ต้องกรอก, yellow = ควรตรวจสอบ

ใช้งานได้ 2 ระดับ:
  - check_text(text)        ตรวจข้อความธรรมดา 1 ก้อน
  - find_suspects(document) ตรวจทั้งเอกสารที่ตัวอ่านคืนมา (ExtractedDocument)
"""

import re
from dataclasses import asdict, dataclass

from app.models import ExtractedDocument

RED = "red"
YELLOW = "yellow"

# ---------- ชุดอักขระภาษาไทย ----------
# เครื่องหมายที่ต้อง "ประกอบ" อยู่กับพยัญชนะ: ไม้หันอากาศ, สระบน/ล่าง, พินทุ, ไม้ไต่คู้, วรรณยุกต์, การันต์ ฯลฯ
THAI_MARKS = "\u0E31\u0E34-\u0E3A\u0E47-\u0E4E"
THAI_TONES = "\u0E48-\u0E4B"                     # ไม้เอก โท ตรี จัตวา
# ตัวอักษรที่ "มีสิทธิ์" อยู่หน้าเครื่องหมายได้ = พยัญชนะ หรือเครื่องหมาย/สระที่ซ้อนกัน
THAI_VALID_BEFORE_MARK = "\u0E01-\u0E2E\u0E30-\u0E3A\u0E47-\u0E4E"

# ---------- รูปแบบ regex ----------
RE_DOUBLE_LEADING_VOWEL = re.compile("\u0E40\u0E40")                     # เเ  (ควรเป็น แ)
RE_DECOMPOSED_SARA_AM = re.compile("\u0E4D\u0E32")                       # ํา  (ควรเป็น ำ)
RE_REPEATED_MARK = re.compile(f"([{THAI_MARKS}\u0E30\u0E32\u0E33])\\1+")  # ้้  ิิ  ะะ
RE_TONE_CONFLICT = re.compile(f"([{THAI_TONES}])(?!\\1)[{THAI_TONES}]")  # ่้ (วรรณยุกต์ซ้อนคนละตัว)
RE_ORPHAN_MARK = re.compile(f"(?<![{THAI_VALID_BEFORE_MARK}])[{THAI_MARKS}]")
RE_EXTRA_SPACES = re.compile(r"(?<=\S) {2,}(?=\S)")
RE_SPACE_BEFORE_PUNCT = re.compile(r"(?<=[^\s.]) +(?=[,;:!?)\]]|\.(?!\.))")
RE_REPEATED_WORD = re.compile(r"\b([A-Za-z]{2,})\s+\1\b", re.IGNORECASE)
RE_DOT_RUN = re.compile(r"[.…]+")                                           # กลุ่มจุดไข่ปลา
RE_CHECKBOX = re.compile(r"\[\s*\]")                                       # ช่องติ๊ก [ ] ในแบบฟอร์ม ช่องว่างข้างในเป็นเรื่องปกติ
RE_MISSING_FIELD = re.compile(r"_{3,}|\[PLEASE ENTER[^\]]*\]")            # เส้นใต้ / ช่องที่ระบบสร้างเอง
RE_LIST_MARKER = re.compile(r"(?:^|\s)(\d{1,3}|[A-Za-z]|[\u0E01-\u0E2E])$")  # "1)" "a)" "ก)" เป็นเลขข้อ

# ---------- ตรวจข้อความเพี้ยน (encoding garble) ----------
GARBLE_MIN_COUNT = 4        # ต้องเจออักขระผิดปกติอย่างน้อยกี่ตัว
GARBLE_MIN_RATIO = 0.40     # และคิดเป็นสัดส่วนของอักขระที่ไม่ใช่ช่องว่างอย่างน้อยเท่าไร


def _is_odd_char(ch: str) -> bool:
    """อักขระที่มักโผล่เมื่อฟอนต์/การเข้ารหัสใน PDF เพี้ยน"""
    code = ord(ch)
    return (
        0x00C0 <= code <= 0x024F   # Latin-1 ตัวมีเครื่องหมาย + Latin Extended-A/B
        or code == 0xFFFD          # ตัวแทนอักขระที่อ่านไม่ได้
        or 0xE000 <= code <= 0xF8FF  # Private Use Area
    )


@dataclass(frozen=True)
class Suspect:
    """จุดสงสัย 1 จุด: บอกว่าอยู่ที่ไหน ทำไมสงสัย และ (ถ้ามั่นใจ) เสนอให้แก้เป็นอะไร"""

    id: str                    # รหัสประจำจุด หน้าเว็บใช้อ้างอิงตอนรับ/ปฏิเสธ
    type: str                  # ชนิด เช่น "THAI_DOUBLE_LEADING_VOWEL" (ให้โปรแกรมใช้)
    severity: str              # "red" หรือ "yellow"
    block_index: int           # อยู่ในก้อนข้อความที่เท่าไร (ตรงกับ Block.index)
    page: int | None           # เลขหน้า (PDF) หรือ None
    start: int                 # ตำแหน่งเริ่มใน block.text
    end: int                   # ตำแหน่งสิ้นสุด (ไม่รวมตัวท้าย แบบ slice ของ Python)
    text: str                  # ข้อความที่สงสัย (ตัดมาจากต้นฉบับ)
    reason: str                # เหตุผลภาษาไทยที่ผู้ใช้อ่านเข้าใจ
    suggestion: str | None     # ข้อเสนอแก้ ถ้าไม่มั่นใจจะเป็น None

    def to_dict(self) -> dict:
        return asdict(self)


def _is_garbled(text: str) -> bool:
    chars = [c for c in text if not c.isspace()]
    if len(chars) < GARBLE_MIN_COUNT:
        return False
    odd = sum(1 for c in chars if _is_odd_char(c))
    return odd >= GARBLE_MIN_COUNT and odd / len(chars) >= GARBLE_MIN_RATIO


def _bracket_problems(text: str) -> list[tuple[int, str]]:
    """หาวงเล็บที่ไม่ครบคู่ คืนค่า [(ตำแหน่ง, อักขระ)]"""
    pairs = {")": "(", "]": "["}
    stack: list[tuple[int, str]] = []
    problems: list[tuple[int, str]] = []
    for i, ch in enumerate(text):
        if ch in "([":
            stack.append((i, ch))
        elif ch in ")]":
            if stack and stack[-1][1] == pairs[ch]:
                stack.pop()
            elif ch == ")" and RE_LIST_MARKER.search(text[:i]):
                continue  # "1)" "a)" "ก)" เป็นเลขข้อ ไม่ใช่วงเล็บผิด
            else:
                problems.append((i, ch))
    problems.extend(stack)
    return problems


def check_text(text: str, block_index: int = 0, page: int | None = None) -> list[Suspect]:
    """ตรวจข้อความ 1 ก้อน คืนรายการจุดสงสัยเรียงตามตำแหน่ง"""
    found: list[Suspect] = []

    def add(type_, severity, start, end, reason, suggestion=None):
        found.append(
            Suspect(
                id=f"s{block_index}-{len(found)}",
                type=type_, severity=severity,
                block_index=block_index, page=page,
                start=start, end=end, text=text[start:end],
                reason=reason, suggestion=suggestion,
            )
        )

    if not text.strip():
        return found

    # --- 1) ข้อความเพี้ยนทั้งก้อน: ถ้าเจอ จะไม่ตรวจกฎอื่นต่อ เพราะจะมีแต่ผลลวง ---
    if _is_garbled(text):
        add("ENCODING_GARBLE", RED, 0, len(text),
            "ข้อความนี้ดูเหมือนอ่านจากไฟล์ได้ไม่ถูกต้อง (ฟอนต์หรือการเข้ารหัสใน PDF อาจเพี้ยน) "
            "กรุณาเทียบกับไฟล์ต้นฉบับ หรือลองอัปโหลดไฟล์ DOCX แทน")
        return found

    # --- 2) ภาษาไทย ---
    for m in RE_DOUBLE_LEADING_VOWEL.finditer(text):
        add("THAI_DOUBLE_LEADING_VOWEL", RED, m.start(), m.end(),
            "พบสระ เ สองตัวติดกัน ซึ่งมักตั้งใจพิมพ์เป็นสระ แ", "แ")

    for m in RE_DECOMPOSED_SARA_AM.finditer(text):
        add("THAI_DECOMPOSED_SARA_AM", RED, m.start(), m.end(),
            "สระ อำ ถูกพิมพ์แยกเป็นนิคหิต (ํ) + สระอา (า) หน้าตาคล้ายกันแต่รหัสอักขระผิด "
            "ทำให้ค้นหาและตรวจคำผิดไม่ได้", "ำ")

    for m in RE_REPEATED_MARK.finditer(text):
        add("THAI_REPEATED_MARK", RED, m.start(), m.end(),
            "พบสระหรือวรรณยุกต์ตัวเดียวกันซ้ำติดกัน", m.group(1))

    for m in RE_TONE_CONFLICT.finditer(text):
        add("THAI_TONE_CONFLICT", RED, m.start(), m.end(),
            "พบวรรณยุกต์สองตัวติดกัน ไม่ทราบว่าตั้งใจใช้ตัวไหน กรุณาตรวจสอบ")

    for m in RE_ORPHAN_MARK.finditer(text):
        add("THAI_ORPHAN_MARK", RED, m.start(), m.end(),
            "พบสระหรือวรรณยุกต์ที่ไม่มีพยัญชนะนำหน้า")

    # --- 3) ช่องว่างและเครื่องหมายวรรคตอน ---
    # ช่องติ๊ก [ ] ในฟอร์มมีช่องว่างข้างในโดยตั้งใจ จึงข้ามตำแหน่งเหล่านั้น
    checkboxes = [m.span() for m in RE_CHECKBOX.finditer(text)]

    def in_checkbox(m) -> bool:
        return any(a <= m.start() and m.end() <= b for a, b in checkboxes)

    for m in RE_EXTRA_SPACES.finditer(text):
        if in_checkbox(m):
            continue
        add("EXTRA_SPACES", YELLOW, m.start(), m.end(),
            "พบช่องว่างติดกันหลายช่อง", " ")

    for m in RE_SPACE_BEFORE_PUNCT.finditer(text):
        if in_checkbox(m):
            continue
        add("SPACE_BEFORE_PUNCT", YELLOW, m.start(), m.end(),
            "มีช่องว่างอยู่หน้าเครื่องหมายวรรคตอน", "")

    for m in RE_REPEATED_WORD.finditer(text):
        add("REPEATED_WORD", YELLOW, m.start(), m.end(),
            "พบคำภาษาอังกฤษซ้ำติดกัน อาจพิมพ์เกิน (ถ้าตั้งใจ ให้กดปฏิเสธได้)", m.group(1))

    for pos, ch in _bracket_problems(text):
        add("UNBALANCED_BRACKET", YELLOW, pos, pos + 1,
            f"วงเล็บ {ch} ไม่มีคู่ที่ตรงกัน")

    # --- 4) ช่องที่ต้องให้ผู้ใช้กรอกเอง ---
    for m in RE_MISSING_FIELD.finditer(text):
        add("MISSING_FIELD", RED, m.start(), m.end(),
            "ช่องนี้ยังว่างหรือเป็นที่ว่างให้กรอก ผู้ใช้ต้องกรอกเอง ระบบจะไม่เดาข้อมูลให้")

    for m in RE_DOT_RUN.finditer(text):
        weight = sum(3 if c == "…" else 1 for c in m.group())  # "…" ตัวเดียวนับเท่าจุด 3 จุด
        standalone = (m.start() == 0 or text[m.start() - 1].isspace()) and (
            m.end() == len(text) or text[m.end()].isspace()
        )
        if weight >= 4:
            add("MISSING_FIELD", RED, m.start(), m.end(),
                "ช่องนี้ยังว่างหรือเป็นที่ว่างให้กรอก ผู้ใช้ต้องกรอกเอง ระบบจะไม่เดาข้อมูลให้")
        elif weight == 3 and standalone:
            add("POSSIBLE_BLANK", YELLOW, m.start(), m.end(),
                "จุดไข่ปลานี้อาจเป็นที่ว่างให้กรอก หรืออาจเป็นเครื่องหมายในประโยคปกติ กรุณาตรวจสอบ")

    # เรียงตามตำแหน่ง แล้วรันรหัสใหม่ให้เรียงตามลำดับที่ผู้ใช้จะเห็น
    found.sort(key=lambda s: (s.start, s.end))
    return [
        Suspect(**{**asdict(s), "id": f"s{block_index}-{i}"})
        for i, s in enumerate(found)
    ]


def find_suspects(document: ExtractedDocument) -> list[Suspect]:
    """ตรวจทุกก้อนในเอกสาร"""
    result: list[Suspect] = []
    for block in document.blocks:
        result.extend(check_text(block.text, block.index, block.page))
    return result