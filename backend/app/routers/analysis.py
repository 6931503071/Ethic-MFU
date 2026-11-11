from fastapi import APIRouter, HTTPException, Path
from app.field_matcher import FieldMatcher
from app.form_fields import load_template
from app.models import ExtractedDocument
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import List, Any, Dict
from pathlib import Path
import logging

from config import settings
from app.ai.client import AIClient, AIError, AnthropicClient, OpenAICompatClient
from app.ai.fill import fill_form_from_blocks
from app.ai.pipeline import draft_form_from_blocks
from app.form_fields import load_template
from app.field_matcher import FieldMatcher
from app.models import ExtractedDocument, Block

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


class FillRequest:
    """Schema สำหรับ request"""
    pass


@router.post("/fill")
async def fill_form(request_data: dict):
    """
    รับ blocks + template_id
    จับคู่กับช่องในแบบฟอร์ม
    คืน FilledForm
    """
    try:
        # ดึง blocks และ template_id จาก request
        blocks = request_data.get("blocks", [])
        template_id = request_data.get("template_id", "ap02_research_proposal")
        
        if not blocks:
            raise HTTPException(status_code=400, detail="ต้องส่ง blocks")
        
        # ✅ แปลง blocks → ExtractedDocument
        doc_blocks = [
            Block(
                index=b.get("index", 0),
                text=b.get("text", ""),
                kind=b.get("kind", "text"),
                page=b.get("page", 1)
            )
            for b in blocks
        ]
        
        temp_doc = ExtractedDocument(
            file_type="pdf",
            page_count=0,
            warnings=[],
            blocks=doc_blocks
        )
        
        # ✅ โหลดเทมเพลต (แปลง Path เป็น str)
        template_dir = Path(__file__).parent.parent.parent / "templates"
        template_path = str(template_dir / f"{template_id}.json")
        
        try:
            template = load_template(template_path)
        except Exception as e:
            logger.error(f"โหลดเทมเพลตล้มเหลว: {e}")
            raise HTTPException(status_code=500, detail=f"โหลดเทมเพลต {template_id} ล้มเหลว: {str(e)}")
        
        # ✅ จับคู่ช่อง (รัน thread pool เพื่อไม่บล็อก)
        try:
            matcher = FieldMatcher(temp_doc, template)
            filled_form = await run_in_threadpool(matcher.match_all_fields)
        except Exception as e:
            logger.error(f"จับคู่ช่องล้มเหลว: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"จับคู่ช่องล้มเหลว: {str(e)}")
        
        # ✅ คืนผลลัพธ์
        return filled_form.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API ล้มเหลว: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"เกิดข้อผิดพลาด: {str(e)}")