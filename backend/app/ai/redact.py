"""
ปิดบังข้อมูลส่วนบุคคลก่อนส่งข้อความให้บริการ AI ภายนอก (ทำในเครื่องเราเท่านั้น)

หลักการ
- แทนข้อมูลที่ตรวจเจอด้วยรหัส เช่น {{EMAIL_1}} แล้วเก็บตารางจับคู่ไว้ในหน่วยความจำ
  ของ Redactor ตัวนั้นเท่านั้น (ไม่เขียนลงไฟล์ ไม่เขียนลง log)
- ค่าเดียวกันได้รหัสเดิมเสมอ เพื่อให้ AI เห็นว่าเป็นสิ่งเดียวกัน
- ใช้รูปแบบ {{...}} เพราะไม่ชนกับรูปแบบ [[ข้อความ|เหตุผล]] ที่หน้าเว็บใช้ไฮไลต์

ข้อจำกัด (สำคัญ ต้องบอกผู้ใช้ตามจริง)
- ตรวจด้วยรูปแบบ (regex) จึงจับได้เฉพาะอีเมล เบอร์โทร เลขบัตรประชาชน เลขยาว 9-12 หลัก
  และชื่อที่ขึ้นต้นด้วยคำนำหน้า (นาย นาง นางสาว ดร. ผศ. ฯลฯ)
- ชื่อที่ไม่มีคำนำหน้า ที่อยู่ ชื่อหมู่บ้าน ชื่อสถานที่ จับไม่ได้ ดังนั้นการปิดบังนี้
  "ลดความเสี่ยง" ไม่ใช่การรับประกันว่าไม่มีข้อมูลส่วนตัวหลุดไปถึงผู้ให้บริการ AI
"""

import re

_TOKEN_RE = re.compile(r"\{\{([A-Z_]+)_(\d+)\}\}")

# ลำดับสำคัญ: แบบที่เฉพาะเจาะจงกว่าต้องมาก่อน ไม่งั้นเลขบัตรจะถูกตีเป็นเบอร์โทร
_TITLES = (
    r"ผศ\.?\s?ดร\.?|รศ\.?\s?ดร\.?|ศ\.?\s?ดร\.?|ผศ\.|รศ\.|ศ\.|ดร\.|นางสาว|นาง|นาย"
    r"|Assoc\.\s?Prof\.|Asst\.\s?Prof\.|Prof\.|Dr\.|Mr\.|Mrs\.|Ms\."
)

_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    # เลขบัตรประชาชน 13 หลัก (มีขีดหรือเว้นวรรคคั่นหรือไม่ก็ได้)
    ("THAI_ID", re.compile(r"(?<!\d)\d[\s-]?\d{4}[\s-]?\d{5}[\s-]?\d{2}[\s-]?\d(?!\d)")),
    # เบอร์โทร 0x-xxx-xxxx / 0xx-xxx-xxxx / +66 ...
    ("PHONE", re.compile(r"(?<![\d])(?:\+66[\s-]?|[0๐])\d{1,2}[\s-]?\d{3}[\s-]?\d{4}(?!\d)")),
    # เลขยาว 9-12 หลักที่เหลือ (เช่น รหัสนักศึกษา เลขบัญชี) ไม่นับตัวเลขที่มีจุลภาค/ทศนิยมติด
    ("ID_NUMBER", re.compile(r"(?<![\d,.])\d{9,12}(?![\d,.])")),
    # ชื่อที่ขึ้นต้นด้วยคำนำหน้า ตามด้วยชื่อ 1-2 คำ (ไทยหรืออังกฤษ)
    (
        "NAME",
        re.compile(
            rf"(?:{_TITLES})\s?(?:[ก-๙]+|[A-Z][a-z]+)(?:\s[ก-๙]+|\s[A-Z][a-z]+)?"
        ),
    ),
]


class Redactor:
    """ใช้ 1 ตัวต่อ 1 งาน (1 เอกสาร) เพื่อให้รหัสและตารางจับคู่ไม่ปนกันข้ามผู้ใช้"""

    def __init__(self) -> None:
        self._value_to_token: dict[str, str] = {}
        self._token_to_value: dict[str, str] = {}
        self._counters: dict[str, int] = {}

    # ไม่ให้ค่าจริงหลุดไปกับ repr/log โดยไม่ตั้งใจ
    def __repr__(self) -> str:
        return f"<Redactor masked={len(self._token_to_value)} items>"

    def _token_for(self, kind: str, value: str) -> str:
        key = f"{kind}:{value}"
        if key in self._value_to_token:
            return self._value_to_token[key]
        n = self._counters.get(kind, 0) + 1
        self._counters[kind] = n
        token = f"{{{{{kind}_{n}}}}}"
        self._value_to_token[key] = token
        self._token_to_value[token] = value
        return token

    def redact(self, text: str) -> str:
        """คืนข้อความที่ปิดบังแล้ว (ข้อความต้นฉบับไม่ถูกแก้)"""
        result = text
        for kind, pattern in _PATTERNS:
            result = pattern.sub(lambda m, k=kind: self._token_for(k, m.group(0)), result)
        return result

    def restore(self, text: str) -> str:
        """แทนรหัสกลับเป็นค่าจริง รหัสที่ไม่รู้จัก (AI สร้างเอง) จะคงไว้ตามเดิม"""
        return _TOKEN_RE.sub(
            lambda m: self._token_to_value.get(m.group(0), m.group(0)), text
        )

    def unknown_tokens(self, text: str) -> list[str]:
        """รหัสในข้อความที่ไม่อยู่ในตารางของเรา = AI แต่งขึ้นเอง ควรปฏิเสธคำตอบนั้น"""
        return [
            m.group(0)
            for m in _TOKEN_RE.finditer(text)
            if m.group(0) not in self._token_to_value
        ]

    def summary(self) -> dict[str, int]:
        """จำนวนที่ปิดบังแยกตามชนิด (ไม่มีค่าจริง) ใช้แสดงผู้ใช้ได้"""
        return dict(self._counters)