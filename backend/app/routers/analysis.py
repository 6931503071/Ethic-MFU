from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import List, Any, Dict

from config import settings
from app.ai.client import AIClient, AIError, AnthropicClient
from app.ai.fill import fill_form_from_blocks
from app.ai.pipeline import draft_form_from_blocks
from app.form_fields import load_template

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
_TEMPLATE_PATH = settings.upload_dir.parent / "ap02.json"   # backend/ap02.json


def get_ai_client() -> AIClient:
    """แยกเป็นฟังก์ชันเพื่อให้ทดสอบสลับเป็นตัวปลอมได้ (กุญแจอ่านจาก .env บนเซิร์ฟเวอร์เท่านั้น)"""
    return AnthropicClient(
        settings.ai_api_key, settings.ai_model,
        timeout=settings.ai_timeout_seconds, max_tokens=settings.ai_max_output_tokens,
    )


class FillRequest(AnalysisRequest):
    mode: str = "draft"    # "draft" = AI วิเคราะห์แล้วสรุป/เรียบเรียงเป็นร่าง | "extract" = คัดลอกตรงตัวเท่านั้น


@router.post("/fill")
async def fill_form(payload: FillRequest):
    if payload.mode not in ("draft", "extract"):
        raise HTTPException(status_code=422, detail={"code": "BAD_MODE", "message": "mode ต้องเป็น draft หรือ extract"})
    template = load_template(_TEMPLATE_PATH)
    try:
        if payload.mode == "draft":
            result = await run_in_threadpool(
                draft_form_from_blocks, template, payload.blocks, get_ai_client(),
                max_input_chars=settings.ai_max_input_chars, chunk_chars=settings.ai_chunk_chars,
                max_chunks=settings.ai_max_chunks, locate_workers=settings.ai_locate_workers,
            )
            stats = result.stats
        else:
            result = await run_in_threadpool(
                fill_form_from_blocks, template, payload.blocks, get_ai_client(),
                max_input_chars=settings.ai_max_input_chars,
            )
            stats = {}
    except AIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    return {
        "mode": payload.mode,
        "form": result.form.to_dict(),
        "progress": result.form.progress(),
        "rejected": [{"field_id": r.field_id, "code": r.code, "message": r.message} for r in result.rejected],
        "redaction_summary": result.redaction_summary,
        "stats": stats,
    }
