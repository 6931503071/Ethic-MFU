"""
ตัวเรียกบริการ AI (ขั้น 6) แยกเป็นชั้นบางๆ เพื่อเปลี่ยนผู้ให้บริการได้โดยไม่แตะส่วนอื่น

- AIClient: สัญญากลางที่ส่วนอื่นใช้ (complete(system, user) -> ข้อความตอบกลับ)
- AnthropicClient: ตัวจริง เรียก https://api.anthropic.com/v1/messages ผ่าน httpx
- AIError: ข้อผิดพลาดที่แปลงเป็นรหัส + ข้อความภาษาไทยให้ผู้ใช้แล้ว
  (ไม่ใส่กุญแจ ไม่ใส่เนื้อหาเอกสาร ไม่ใส่ response ดิบของผู้ให้บริการ)

หมายเหตุความเป็นส่วนตัว: ฟังก์ชันที่เรียก client ต้องส่งเฉพาะข้อความที่ผ่าน Redactor แล้ว
ไฟล์นี้ไม่บันทึกเนื้อหา prompt หรือคำตอบลง log
"""

from __future__ import annotations

import logging
from typing import Protocol

import httpx

logger = logging.getLogger(__name__)

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"


class AIError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 502):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message}


class AIClient(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class AnthropicClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        timeout: float = 60.0,
        max_tokens: int = 8000,
        transport: httpx.BaseTransport | None = None,   # ไว้ทดสอบโดยไม่ยิงเน็ตจริง
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._max_tokens = max_tokens
        self._transport = transport

    def __repr__(self) -> str:                  # ไม่ให้กุญแจหลุดไปกับ repr/log
        return f"<AnthropicClient model={self._model}>"

    def complete(self, system: str, user: str) -> str:
        if not self._api_key:
            raise AIError("AI_NOT_CONFIGURED", "ยังไม่ได้ตั้งค่ากุญแจ AI ที่เซิร์ฟเวอร์", 503)
        body = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": API_VERSION,
            "content-type": "application/json",
        }
        try:
            with httpx.Client(timeout=self._timeout, transport=self._transport) as http:
                resp = http.post(API_URL, json=body, headers=headers)
        except httpx.TimeoutException:
            raise AIError("AI_TIMEOUT", "AI ตอบช้าเกินกำหนด กรุณาลองใหม่อีกครั้ง", 504) from None
        except httpx.HTTPError:
            raise AIError("AI_UNREACHABLE", "เชื่อมต่อบริการ AI ไม่ได้ กรุณาตรวจอินเทอร์เน็ตแล้วลองใหม่", 502) from None

        if resp.status_code in (401, 403):
            raise AIError("AI_AUTH", "กุญแจ AI ไม่ถูกต้องหรือไม่มีสิทธิ์ใช้งาน (แจ้งผู้ดูแลระบบ)", 502)
        if resp.status_code == 429:
            raise AIError("AI_RATE_LIMIT", "ใช้งาน AI ถี่เกินกำหนด กรุณารอสักครู่แล้วลองใหม่", 429)
        if resp.status_code >= 500:
            raise AIError("AI_UNAVAILABLE", "บริการ AI ขัดข้องชั่วคราว กรุณาลองใหม่ภายหลัง", 502)
        if resp.status_code != 200:
            logger.error("AI ตอบรหัส %s", resp.status_code)      # ไม่ log เนื้อหา
            raise AIError("AI_BAD_REQUEST", "บริการ AI ปฏิเสธคำขอ", 502)

        try:
            data = resp.json()
            text = "".join(b.get("text", "") for b in data["content"] if b.get("type") == "text")
        except (ValueError, KeyError, TypeError, AttributeError):
            raise AIError("AI_BAD_RESPONSE", "อ่านคำตอบจาก AI ไม่ได้", 502) from None
        if not text.strip():
            raise AIError("AI_BAD_RESPONSE", "AI ไม่ได้ตอบข้อความกลับมา", 502)
        return text