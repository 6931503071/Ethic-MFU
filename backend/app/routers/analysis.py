import logging
from pathlib import Path
from typing import Any, Dict, List, Literal

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from config import settings
from app.ai.client import AIClient, AIError, AnthropicClient, OpenAICompatClient
from app.ai.fill import fill_form_from_blocks
from app.ai.pipeline import draft_form_from_blocks
from app.form_fields import load_template

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analysis", tags=["Analysis"])

# กำหนด Schema รับข้อมูลที่ได้จาก PDF
class AnalysisRequest(BaseModel):
    filename: str
    blocks: List[Dict[str, Any]]

@router.post("/check")
async def check_ethics(payload: AnalysisRequest):
    # รวมข้อความสกัดทั้งหมดเข้าด้วยกัน
    full_text = " ".join([b.get("text", "") for b in payload.blocks])
    
    # ตัวอย่าง Logic ตรวจสอบเบื้องต้น
    has_informed_consent = "หนังสือยินยอม" in full_text or "Informed Consent" in full_text
    has_pdpa = "คุ้มครองข้อมูล" in full_text or "PDPA" in full_text
    
    return {
        "status": "success",
        "filename": payload.filename,
        "summary": {
            "total_blocks": len(payload.blocks),
            "has_informed_consent": has_informed_consent,
            "has_pdpa": has_pdpa
        },
        "recommendations": [
            "ตรวจสอบกลุ่มตัวอย่างเปราะบางเพิ่มเติม",
            "ระบุมาตรการเก็บรักษาความลับของข้อมูลวิจัย"
        ]
    }


# ---------- ขั้น 6: ให้ AI เติมฟอร์มจากข้อความที่อ่านแล้ว ----------

def get_ai_client() -> AIClient:
    """แยกเป็นฟังก์ชันเพื่อให้ทดสอบสลับเป็นตัวปลอมได้ (กุญแจอ่านจาก .env บนเซิร์ฟเวอร์เท่านั้น)"""
    if settings.ai_provider == "openai_compat":
        if not settings.ai_base_url:
            raise AIError("AI_NOT_CONFIGURED", "ยังไม่ได้ตั้งค่า AI_BASE_URL ที่เซิร์ฟเวอร์", 503)
        return OpenAICompatClient(
            settings.ai_api_key, settings.ai_model, settings.ai_base_url,
            timeout=settings.ai_timeout_seconds, max_tokens=settings.ai_max_output_tokens,
        )
    return AnthropicClient(
        settings.ai_api_key, settings.ai_model,
        timeout=settings.ai_timeout_seconds, max_tokens=settings.ai_max_output_tokens,
    )


# เทมเพลตเต็ม (111 ช่อง) ตัวเดียวกับที่หน้าเว็บใช้ (templates/ap02.json) ห้ามใช้ backend/templates/ ซึ่งเป็นตัวย่อ 12 ช่อง
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATE_FILES = {"ap02_research_proposal": BACKEND_DIR / "ap02.json"}


class FillRequest(BaseModel):
    filename: str = ""
    blocks: List[Dict[str, Any]]
    mode: Literal["draft", "extract"] = "draft"      # draft = AI สรุป/เรียบเรียง, extract = คัดลอกตรงต้นฉบับ
    template_id: str = "ap02_research_proposal"
    language: Literal["th", "en"] = "th"


@router.post("/fill")
async def fill_form(req: FillRequest):
    """ให้ AI อ่านข้อความจากไฟล์แล้วเติมช่องของแบบฟอร์ม
    คืน {mode, form, accepted, rejected, redaction_summary, stats} (หน้าเว็บอ่าน form.values)"""
    if not req.blocks:
        raise HTTPException(status_code=400, detail="ต้องส่ง blocks")

    template_path = TEMPLATE_FILES.get(req.template_id)
    if template_path is None:
        raise HTTPException(status_code=422, detail=f"ไม่รู้จักเทมเพลต {req.template_id}")
    try:
        template = load_template(template_path)
    except Exception:
        logger.exception("โหลดเทมเพลตล้มเหลว")
        raise HTTPException(status_code=500, detail="โหลดเทมเพลตล้มเหลว")

    try:
        client = get_ai_client()
        fn = draft_form_from_blocks if req.mode == "draft" else fill_form_from_blocks
        kwargs: Dict[str, Any] = {"language": req.language, "max_input_chars": settings.ai_max_input_chars}
        if req.mode == "draft":
            kwargs.update(
                chunk_chars=settings.ai_chunk_chars,
                max_chunks=settings.ai_max_chunks,
                locate_workers=settings.ai_locate_workers,
            )
        result = await run_in_threadpool(fn, template, req.blocks, client, **kwargs)
    except AIError as e:
        logger.warning("AI ล้มเหลว: %s", e.code)
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    except Exception:
        logger.exception("AI ล้มเหลวแบบไม่คาดคิด")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดภายในระบบ AI")

    return {
        "mode": req.mode,
        "form": result.form.to_dict(),
        "accepted": [{"field_id": a.field_id, "source_blocks": list(a.source_blocks)} for a in result.accepted],
        "rejected": [
            {"field_id": r.field_id, "code": r.code, "message": r.message} for r in result.rejected
        ],
        "redaction_summary": result.redaction_summary,
        "stats": getattr(result, "stats", {}),
    }