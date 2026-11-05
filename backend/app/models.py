"""
โครงสร้างข้อมูลกลางที่ตัวอ่านทุกตัวต้องคืนค่าออกมาให้เหมือนกัน
ไม่ว่าต้นทางจะเป็น PDF หรือ DOCX ส่วนที่อยู่ถัดไป (ตัวตรวจจุดสงสัย, ตัวสร้างเอกสาร)
จะเห็นหน้าตาข้อมูลเดียวกันเสมอ
"""

from dataclasses import dataclass, field

@dataclass(frozen=True)
class Block:
    """ข้อความ 1 ก้อน (ส่วนใหญ่คือ 1 ย่อหน้า) ที่อ่านมาจากไฟล์ต้นฉบับ"""

    index: int          # ลำดับก้อนในเอกสาร (0, 1, 2, ...) ไว้เรียงและอ้างอิง
    text: str           # ข้อความ "ตามต้นฉบับ" ห้ามแก้ไขที่ขั้นอ่าน
    kind: str           # "paragraph" | "heading" | "table_cell"
    page: int | None    # เลขหน้าใน PDF (เริ่มที่ 1) / DOCX ไม่มีหน้าตายตัว จึงเป็น None


@dataclass(frozen=True)
class ReadWarning:
    """ข้อสังเกตเกี่ยวกับการอ่านไฟล์ ไม่ใช่ข้อผิดพลาดร้ายแรง แต่ผู้ใช้ควรรู้"""

    code: str           # เช่น "NO_TEXT_LAYER" (ให้โปรแกรมใช้)
    message: str        # ข้อความภาษาไทยให้ผู้ใช้อ่าน
    page: int | None = None


@dataclass
class ExtractedDocument:
    """ผลลัพธ์รวมของการอ่าน 1 ไฟล์"""

    file_type: str                       # "pdf" หรือ "docx" (ตรงกับ extension ใน ValidatedFile ที่ตัดจุดออก)
    page_count: int | None               # DOCX ไม่ทราบจำนวนหน้า จึงเป็น None
    blocks: list[Block] = field(default_factory=list)
    warnings: list[ReadWarning] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        """รวมข้อความทุกก้อน คั่นด้วยบรรทัดว่าง เหมาะกับการดูภาพรวมหรือส่งให้ AI"""
        return "\n\n".join(b.text for b in self.blocks)

    @property
    def is_empty(self) -> bool:
        return not any(b.text.strip() for b in self.blocks)