# รับข้อมูล 860 บล็อก จากไฟล์ที่อ่านได้
# ดูช่องในแบบฟอร์ม AP02 (ดึงจาก templates/ap02.json)
# ใช้ logic ค้นหา (keyword matching + fuzzy matching) เพื่อจับคู่
# บอกระบบ: "ช่อง title_th = ข้อความจากบล็อค 5 และ 6" คืนผลเป็น `FilledForm` ที่มีค่าในแต่ละช่อง

from ast import keyword
from email.mime import text
from typing import Optional, Tuple
from difflib import SequenceMatcher
from pathlib import Path

from numpy import block
from app.models import ExtractedDocument, Block
from app.form_fields import FieldDef, FormTemplate, FillBy
from app.filled_form import FilledForm, ValueStatus
from app.models import Block

class FieldMatcher:
    """จับคู่ข้อความจากไฟล์กับช่องในแบบฟอร์ม"""
    
    def __init__(self, doc: ExtractedDocument, template: FormTemplate):
        self.doc = doc
        self.template = template
        self.blocks = doc.blocks  # 860 ส่วน
        self.text_index = self._build_index()  # เรียงบล็อก เก็บ index
    
    def _build_index(self) -> dict[int, str]:
        """สร้าง dict { block_index -> block_text } ให้ค้นหาเร็ว"""
        return {b.index: b.text for b in self.blocks}
    
    def match_all_fields(self) -> FilledForm:
        """จับคู่ทุกช่อง คืน FilledForm พร้อมค่า"""
        form = FilledForm.blank(self.template)
        
        for field in self.template.iter_fields():
            if field.fill_by != FillBy.AI:
                # ช่องผู้ใช้ (fill_by="user") ข้ามไป
                continue
            
            result = self.find_value_for_field(field)
            if result:
                value, block_indices = result
                form.set_found(field.id, value, tuple(block_indices))
        
        return form
    
    def find_value_for_field(self, field: FieldDef) -> Optional[Tuple[str, list[int]]]:
        """ค้นหาค่าสำหรับช่องหนึ่ง คืน (value, block_indices) หรือ None"""
        
        # 1. สร้างกำหนดคำสำคัญ
        keywords = self._get_keywords_for_field(field)
        
        # 2. ค้นหาในบล็อก
        for keyword in keywords:
            result = self._search_blocks(keyword, field)
            if result:
                return result
        
        return None
    
    def _get_keywords_for_field(self, field: FieldDef) -> list[str]:
        """สร้างรายการคำสำคัญสำหรับช่อง"""
        keywords = []
        
        # เพิ่ม label (ทั้งไทยและอังกฤษ)
        if field.label:
            keywords.append(field.label)
        if field.label_en:
            keywords.append(field.label_en)
        
        # เพิ่มหมวด (section title)
        if field.section_id:
            section = self.template.get_section(field.section_id)
            if section.title:
                keywords.append(section.title)
            if section.title_en:
                keywords.append(section.title_en)
        
        # เพิ่มคำที่เกี่ยวข้องเฉพาะช่อง
        related = self._get_related_terms(field.id)
        keywords.extend(related)
        
        return keywords
    
    def _search_blocks(self, keyword: str, field: FieldDef) -> Optional[Tuple[str, list[int]]]:
        """ค้นหา keyword ในบล็อก (exact + fuzzy)"""
        
        found_blocks = []
        
        for block in self.blocks:
            # Exact match
            if keyword.lower() in block.text.lower():
                found_blocks.append(block)
            # Fuzzy match (เลือกที่มีความคล้ายคลึง >= 85%)
            elif self._similarity(keyword, block.text) >= 0.85:
                found_blocks.append(block)
        
        if not found_blocks:
            return None
        
        # เลือกบล็อกที่เหมาะสม (โดยปกติบล็อกแรกหรือบล็อกที่ใกล้หลังคำคำสำคัญ)
        best_block = self._select_best_block(found_blocks, keyword)
        
        # ดึงค่าจากบล็อก (ข้อความหลังคำคำสำคัญ)
        value = self._extract_value_from_block(best_block, keyword, field)
        
        if value and value.strip():
            return (value, [best_block.index])
        
        return None
    
    def _similarity(self, a: str, b: str) -> float:
        """คำนวณความคล้ายคลึง 0-1"""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def _select_best_block(self, blocks: list[Block], keyword: str) -> Block:
        """เลือกบล็อกที่เหมาะสมที่สุด"""
        # เรียงตามลำดับการปรากฏ (block หลังคำสำคัญ)
        return blocks[0]
    
    def _extract_value_from_block(self, block: Block, keyword: str, field: FieldDef) -> str:
        idx = block.text.lower().find(keyword.lower())
        if idx == -1:
            return ""
    
        after_keyword = block.text[idx + len(keyword):].strip()
    
    # ถ้าว่าง ดึงจากบล็อกถัดไป
        if not after_keyword and block.index + 1 < len(self.blocks):
            next_block = self.blocks[block.index + 1]
            after_keyword = next_block.text.strip()
    
        lines =  after_keyword.split('\n')
        value = lines[0].strip()
        return value.strip()
    
    def _get_related_terms(self, field_id: str) -> list[str]:
        mapping = {
        "title_th": ["Research Title", "ชื่อโครงการ"],
        "title_en": ["English Title", "ชื่อภาษาอังกฤษ"],
        "field_of_study": ["Field of Research", "สาขาวิชา"],
        "pi_name": ["Principal Investigator", "ชื่อ สกุล"],
        "pi_affiliation": ["Department", "Faculty", "หน่วยงาน"],
        "pi_address": ["Address", "ที่อยู่"],
        "pi_phone": ["Phone", "เบอร์โทร"],
        "pi_email": ["Email", "อีเมล"],
        # ... เพิ่มเติมทั้งหมด
        }
        return mapping.get(field_id, [])

    def _normalize_text(self, text: str) -> str:
        """ลบช่องว่าง เครื่องหมาย"""
        text = " ".join(text.split())
        text = text.replace("(", "").replace(")", "").replace(":", "").replace("-", "")
        return text

    def _search_blocks(self, keyword: str, field: FieldDef):
        keyword_norm = self._normalize_text(keyword)
        found_blocks = []

        for block in self.blocks:
            block_norm = self._normalize_text(block.text)
        
            # Exact match
            if keyword_norm.lower() in block_norm.lower():
                found_blocks.append(block)
            # Fuzzy match
            elif self._similarity(keyword_norm, block_norm) >= 0.80:
                found_blocks.append(block)

    def _normalize_text(self, text: str) -> str:
        """ทำให้ข้อความเป็นมาตรฐาน (ลบช่องว่าง เครื่องหมาย)"""
        # ลบช่องว่างหลาย ๆ ตัวให้เป็นตัวเดียว
        text = " ".join(text.split())
        # ลบเครื่องหมายวรรคตอนบางตัว
        for char in "()：-–—":
            text = text.replace(char, "")
        return text           