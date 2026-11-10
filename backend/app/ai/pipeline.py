"""
โหมด "ร่างจาก AI" ทั้งสายงาน: ไฟล์ -> ปิดบังข้อมูลส่วนตัว -> (ไฟล์ยาว: ให้ AI หาส่วนที่เกี่ยวข้อง)
-> ให้ AI ร่างข้อความทุกช่อง -> ตรวจร่าง (draft_check) -> เติมฟอร์มด้วยสถานะ AI_DRAFT

ไฟล์สั้น (รวมไม่เกิน max_input_chars): เรียก AI ครั้งเดียวพร้อมทั้งเอกสาร
ไฟล์ยาว: 1) แบ่งเอกสารเป็นก้อน ให้ AI ชี้ว่าบล็อกไหนเกี่ยวกับช่องไหน (เรียกขนานกันได้)
2) รวมบล็อกที่ชี้ไว้ (แบ่งโควตาให้ทุกช่องเท่าๆ กัน) แล้วเรียก AI ร่างครั้งเดียว
ผู้ใช้ไม่ต้องจัดหัวข้อในไฟล์ให้ตรงฟอร์ม
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Iterable

from app.ai.answer_check import Accepted, Rejected
from app.ai.client import AIClient, AIError
from app.ai.draft_check import apply_drafts, check_drafts
from app.ai.fill import parse_ai_json
from app.ai.prompts import (
    DRAFT_SYSTEM_PROMPT,
    LOCATE_SYSTEM_PROMPT,
    build_draft_prompt,
    build_locate_prompt,
    draftable_fields,
)
from app.ai.redact import Redactor
from app.filled_form import FilledForm
from app.form_fields import FormTemplate

MAX_LOCATED_PER_FIELD = 12


@dataclass
class DraftResult:
    form: FilledForm
    accepted: list[Accepted]
    rejected: list[Rejected]
    redaction_summary: dict[str, int] = field(default_factory=dict)
    stats: dict[str, int] = field(default_factory=dict)     # จำนวนก้อน/บล็อกที่ใช้ (ไม่มีเนื้อหา)


def split_chunks(block_texts: dict[int, str], chunk_chars: int) -> list[dict[int, str]]:
    """แบ่งตามลำดับเอกสาร ก้อนละไม่เกิน chunk_chars (บล็อกเดียวที่ยาวเกินก็อยู่ก้อนของตัวเอง)"""
    chunks: list[dict[int, str]] = []
    cur: dict[int, str] = {}
    size = 0
    for i in sorted(block_texts):
        t = block_texts[i]
        if cur and size + len(t) > chunk_chars:
            chunks.append(cur)
            cur, size = {}, 0
        cur[i] = t
        size += len(t)
    if cur:
        chunks.append(cur)
    return chunks


def _locate_chunk(client: AIClient, template: FormTemplate, chunk: dict[int, str], valid_fields: set[str]) -> dict[str, list[int]]:
    raw = parse_ai_json(client.complete(LOCATE_SYSTEM_PROMPT, build_locate_prompt(template, chunk)))
    out: dict[str, list[int]] = {}
    items = raw.get("locate") if isinstance(raw, dict) else None
    for it in items if isinstance(items, list) else []:
        if not isinstance(it, dict) or it.get("field_id") not in valid_fields:
            continue
        ids = [i for i in (it.get("blocks") or []) if isinstance(i, int) and not isinstance(i, bool) and i in chunk]
        if ids:
            out.setdefault(it["field_id"], []).extend(ids)
    return out


def select_context(located: dict[str, list[int]], block_texts: dict[int, str], budget: int) -> dict[int, str]:
    """เลือกบล็อกให้พอดีงบตัวอักษร โดยแบ่งโควตาเป็นรอบ: รอบที่ k เอาบล็อกลำดับที่ k ของทุกช่อง
    เพื่อไม่ให้ช่องหนึ่งกินที่ทั้งหมด"""
    chosen: dict[int, str] = {}
    used = 0
    for k in range(MAX_LOCATED_PER_FIELD):
        for fid in sorted(located):
            ids = located[fid]
            if k >= len(ids) or ids[k] in chosen:
                continue
            t = block_texts[ids[k]]
            if used + len(t) > budget:
                continue
            chosen[ids[k]] = t
            used += len(t)
    return chosen


def draft_form_from_blocks(
    template: FormTemplate,
    blocks: Iterable[dict],
    client: AIClient,
    *,
    language: str = "th",
    max_input_chars: int = 60000,
    chunk_chars: int = 100000,
    max_chunks: int = 12,
    locate_workers: int = 3,
) -> DraftResult:
    redactor = Redactor()
    block_texts: dict[int, str] = {}
    for b in blocks:
        idx, text = b.get("index"), b.get("text")
        if isinstance(idx, int) and not isinstance(idx, bool) and isinstance(text, str) and text.strip():
            block_texts[idx] = redactor.redact(text)
    if not block_texts:
        raise AIError("NO_TEXT", "ไม่มีข้อความให้ AI วิเคราะห์", 422)

    stats = {"blocks": len(block_texts), "chunks": 1, "context_blocks": len(block_texts)}
    total = sum(len(t) for t in block_texts.values())
    context = block_texts

    if total > max_input_chars:
        chunks = split_chunks(block_texts, chunk_chars)
        stats["chunks"] = len(chunks)
        if len(chunks) > max_chunks:
            raise AIError("INPUT_TOO_LARGE", "เอกสารยาวเกินกว่าที่ระบบรองรับ กรุณาแบ่งไฟล์ให้สั้นลง", 413)

        valid = {f.id for f in draftable_fields(template)}
        located: dict[str, list[int]] = {}
        with ThreadPoolExecutor(max_workers=max(1, locate_workers)) as pool:
            for part in pool.map(lambda c: _locate_chunk(client, template, c, valid), chunks):
                for fid, ids in part.items():
                    located.setdefault(fid, []).extend(i for i in ids if i not in located.get(fid, []))
        located = {fid: ids[:MAX_LOCATED_PER_FIELD] for fid, ids in located.items()}
        context = select_context(located, block_texts, max_input_chars)
        stats["context_blocks"] = len(context)
        if not context:
            form = FilledForm.blank(template, language)
            return DraftResult(
                form, [], [Rejected(None, "NOTHING_LOCATED", "AI ไม่พบส่วนของเอกสารที่เกี่ยวข้องกับช่องใดเลย")],
                redactor.summary(), stats,
            )

    raw = parse_ai_json(client.complete(DRAFT_SYSTEM_PROMPT, build_draft_prompt(template, context)))
    accepted, rejected = check_drafts(raw, template, context, redactor)
    form = FilledForm.blank(template, language)
    apply_drafts(form, accepted)
    return DraftResult(form, accepted, rejected, redactor.summary(), stats)
