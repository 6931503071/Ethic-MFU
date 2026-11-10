"""
ข้อผิดพลาดของขั้น "อ่านไฟล์"

ใช้เมื่ออ่านไฟล์ไม่ได้เลย เช่น ไฟล์เสียหาย หรือ PDF ติดรหัสผ่าน
ส่วนกรณีที่ยังอ่านได้แต่ควรให้ผู้ใช้รู้ (เช่น บางหน้าไม่มีข้อความ)
ไม่ต้องใช้ไฟล์นี้ ให้ใช้ ReadWarning ใน models.py แทน
"""


class DocumentReadError(Exception):
    """อ่านเอกสารไม่สำเร็จ พร้อมรหัสสำหรับโปรแกรมและข้อความสำหรับผู้ใช้ (ไทย/อังกฤษ)"""

    def __init__(self, code: str, message: str, message_en: str | None = None):
        super().__init__(message)
        self.code = code            # เช่น "DOCX_CORRUPT" (ให้โปรแกรมใช้แยกกรณี)
        self.message = message      # ข้อความภาษาไทย (คงไว้เพื่อให้โค้ดเดิมใช้ได้)
        self.message_th = message
        # ถ้ายังไม่ได้ใส่ภาษาอังกฤษ ใช้ข้อความไทยแทนไปก่อน ให้ frontend มีข้อความเสมอ
        self.message_en = message_en or message

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "message_th": self.message_th,
            "message_en": self.message_en,
        }