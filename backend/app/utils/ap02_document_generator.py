"""
AP02 Document Generator
Converts form data into AP02/2026 document format (HTML/DOCX)
"""

from typing import Dict, Any, List
import json
from datetime import datetime


class AP02DocumentGenerator:
    """Generate AP02 format documents from form data"""

    def __init__(self):
        self.form_version = "AP 02/2026"
        self.generated_date = datetime.now().strftime("%Y-%m-%d")

    def generate_html(self, form_data: Dict[str, Any]) -> str:
        """
        Generate AP02 document as HTML
        Preserves original formatting as closely as possible

        Parameters:
        - form_data: Dictionary of field_id -> value mappings

        Returns:
        - HTML string representing the AP02 document
        """

        html = f"""<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AP 02/2026 - Research Protocol Proposal</title>
    <style>
        * {{
            font-family: 'Times New Roman', Times, serif;
            margin: 0;
            padding: 0;
        }}

        body {{
            background: white;
            color: #000;
            line-height: 1.6;
        }}

        .page {{
            max-width: 210mm;
            height: 297mm;
            margin: 20px auto;
            padding: 20mm;
            background: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}

        .page-break {{
            page-break-after: always;
            margin-top: 40px;
        }}

        .document-header {{
            text-align: center;
            border-bottom: 3px solid #000;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }}

        .document-header h1 {{
            font-size: 18px;
            font-weight: bold;
            margin: 10px 0;
            text-transform: uppercase;
        }}

        .document-header p {{
            font-size: 12px;
            margin: 5px 0;
        }}

        .section {{
            margin: 25px 0;
            page-break-inside: avoid;
        }}

        .section-number {{
            font-weight: bold;
            font-size: 14px;
            margin-bottom: 10px;
        }}

        .section-title {{
            font-weight: bold;
            font-size: 13px;
            margin: 15px 0 10px;
            text-decoration: underline;
        }}

        .form-row {{
            margin: 12px 0;
            display: flex;
            gap: 20px;
        }}

        .form-row.full {{
            flex-direction: column;
        }}

        .form-field {{
            flex: 1;
            margin-bottom: 12px;
        }}

        .form-field label {{
            font-weight: bold;
            font-size: 12px;
            display: block;
            margin-bottom: 4px;
        }}

        .form-field .required::after {{
            content: " *";
            color: red;
        }}

        .form-field input,
        .form-field textarea,
        .form-field select {{
            width: 100%;
            padding: 6px;
            border: 1px solid #000;
            font-family: inherit;
            font-size: 11px;
            box-sizing: border-box;
        }}

        .form-field textarea {{
            min-height: 60px;
            resize: vertical;
        }}

        .field-value {{
            padding: 6px;
            border-bottom: 1px solid #000;
            min-height: 20px;
            font-size: 11px;
        }}

        .table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
            font-size: 11px;
        }}

        .table th,
        .table td {{
            border: 1px solid #000;
            padding: 8px;
            text-align: left;
        }}

        .table th {{
            background: #f0f0f0;
            font-weight: bold;
        }}

        .page-footer {{
            text-align: center;
            font-size: 10px;
            margin-top: 30px;
            color: #666;
        }}

        .section-divider {{
            border-top: 2px solid #000;
            margin: 20px 0;
        }}

        .missing-data {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 8px;
            margin: 5px 0;
            color: #856404;
            font-weight: bold;
        }}

        .empty-field {{
            background: #fff3cd;
        }}

        @media print {{
            body {{
                margin: 0;
                padding: 0;
            }}

            .page {{
                margin: 0;
                padding: 20mm;
                box-shadow: none;
                page-break-after: always;
            }}
        }}

        .document-info {{
            font-size: 10px;
            color: #666;
            margin: 10px 0;
            padding: 10px;
            background: #f9f9f9;
            border: 1px solid #e0e0e0;
        }}
    </style>
</head>
<body>
"""

        # Add document header
        html += self._generate_header(form_data)

        # Add sections
        html += self._generate_section_1(form_data)
        html += self._generate_section_2(form_data)
        html += self._generate_section_3(form_data)
        html += self._generate_section_4(form_data)
        html += self._generate_section_5(form_data)
        html += self._generate_section_6(form_data)
        html += self._generate_section_7(form_data)
        html += self._generate_section_8(form_data)
        html += self._generate_section_9(form_data)
        html += self._generate_section_10(form_data)
        html += self._generate_section_11(form_data)
        html += self._generate_section_12(form_data)
        html += self._generate_section_14(form_data)
        html += self._generate_section_17(form_data)

        # Add footer
        html += self._generate_footer()

        html += """
</body>
</html>
"""

        return html

    def _generate_header(self, form_data: Dict) -> str:
        """Generate document header"""
        project_title_th = form_data.get('project_title_th', '[ชื่อโครงการ - ไทย]')
        project_title_en = form_data.get('project_title_en', '[Project Title - English]')

        return f"""
<div class="page">
    <div class="document-header">
        <p>Version: {self.form_version}</p>
        <p>Date: {self.generated_date}</p>
        <h1>AP 02/2026</h1>
        <h1>แบบเสนอโครงการวิจัยเพื่อพิจารณา</h1>
        <h1>Research Protocol Proposal Form for Ethical Review</h1>
    </div>

    <div class="document-info">
        ⓘ Generated: {self.generated_date} | Form Version: {self.form_version}
    </div>
"""

    def _generate_section_1(self, form_data: Dict) -> str:
        """Section 1: Research Project Title"""
        title_th = form_data.get('project_title_th', '')
        title_en = form_data.get('project_title_en', '')

        return f"""
    <div class="section">
        <div class="section-number">1. ชื่อโครงการวิจัย (Research Project Title)</div>

        <div class="form-row full">
            <div class="form-field">
                <label>ชื่อโครงการ (ไทย) <span class="required">*</span></label>
                <div class="field-value {'empty-field' if not title_th else ''}">{title_th or '[กรอกชื่อโครงการภาษาไทย]'}</div>
            </div>

            <div class="form-field">
                <label>Project Title (English) <span class="required">*</span></label>
                <div class="field-value {'empty-field' if not title_en else ''}">{title_en or '[Enter English title]'}</div>
            </div>
        </div>
    </div>
"""

    def _generate_section_2(self, form_data: Dict) -> str:
        """Section 2: Field of Research"""
        field_of_study = form_data.get('field_of_study', '')
        subspecialty = form_data.get('field_subspecialty', '')

        return f"""
    <div class="section">
        <div class="section-number">2. สาขาวิชาที่ทำการวิจัย (Field of Research)</div>

        <div class="form-row full">
            <div class="form-field">
                <label>สาขาวิชา <span class="required">*</span></label>
                <div class="field-value {'empty-field' if not field_of_study else ''}">{field_of_study or '[เลือกสาขาวิชา]'}</div>
            </div>

            <div class="form-field">
                <label>สาขาย่อย (ตัวอย่าง: อายุรศาสตร์, ศัลยศาสตร์)</label>
                <div class="field-value">{subspecialty or '[ไม่ระบุ]'}</div>
            </div>
        </div>
    </div>
"""

    def _generate_section_3(self, form_data: Dict) -> str:
        """Section 3: Investigators, Co-Investigators, and Research Advisor"""
        pi_title = form_data.get('principal_investigator_title', '')
        pi_dept = form_data.get('principal_investigator_dept', '')
        pi_email = form_data.get('principal_investigator_email', '')

        return f"""
    <div class="section">
        <div class="section-number">3. ผู้วิจัย ผู้วิจัยรวม และที่ปรึกษา (Investigators & Research Advisor)</div>

        <div class="section-title">3.1 ผู้วิจัยหลัก (Principal Investigator)</div>
        <div class="form-row full">
            <div class="form-field">
                <label>ตำแหน่งวิชาการ-ชื่อ-สกุล <span class="required">*</span></label>
                <div class="field-value {'empty-field' if not pi_title else ''}">{pi_title or '[กรอกชื่อและตำแหน่ง]'}</div>
            </div>

            <div class="form-field">
                <label>สาขาวิชาและหน่วยงาน <span class="required">*</span></label>
                <div class="field-value {'empty-field' if not pi_dept else ''}">{pi_dept or '[กรอกสาขาวิชาและหน่วยงาน]'}</div>
            </div>

            <div class="form-field">
                <label>อีเมล <span class="required">*</span></label>
                <div class="field-value {'empty-field' if not pi_email else ''}">{pi_email or '[กรอกอีเมล]'}</div>
            </div>
        </div>
    </div>
"""

    def _generate_section_4(self, form_data: Dict) -> str:
        """Section 4: Study Period"""
        start_month = form_data.get('start_month', '')
        duration = form_data.get('duration_months', '')
        end_month = form_data.get('end_month', '')

        return f"""
    <div class="section">
        <div class="section-number">4. ช่วงเวลาที่ทำการวิจัย (Study Period)</div>

        <div class="form-row">
            <div class="form-field">
                <label>เดือนที่เริ่มเก็บข้อมูล <span class="required">*</span></label>
                <div class="field-value {'empty-field' if not start_month else ''}">{start_month or '[เลือกวันที่]'}</div>
            </div>

            <div class="form-field">
                <label>ระยะเวลา (เดือน) <span class="required">*</span></label>
                <div class="field-value {'empty-field' if not duration else ''}">{duration or '[จำนวนเดือน]'}</div>
            </div>

            <div class="form-field">
                <label>เดือนที่สิ้นสุด <span class="required">*</span></label>
                <div class="field-value {'empty-field' if not end_month else ''}">{end_month or '[เลือกวันที่]'}</div>
            </div>
        </div>
    </div>
"""

    def _generate_section_5(self, form_data: Dict) -> str:
        """Section 5: Study Site"""
        study_site = form_data.get('study_site_description', '')

        return f"""
    <div class="section">
        <div class="section-number">5. สถานที่ทำการวิจัย (Study Site)</div>

        <div class="form-row full">
            <div class="form-field">
                <label>ระบุสถาบัน (สถาบันเดียว/สหสถาบัน) <span class="required">*</span></label>
                <div class="field-value {'empty-field' if not study_site else ''}" style="min-height: 60px;">{study_site or '[ระบุสถานที่ทำการวิจัย]'}</div>
            </div>
        </div>
    </div>
"""

    def _generate_section_6(self, form_data: Dict) -> str:
        """Section 6: Background & Significance"""
        background = form_data.get('background_significance', '')

        return f"""
    <div class="section">
        <div class="section-number">6. ความสำคัญของปัญหา (Background & Significance)</div>

        <div class="form-row full">
            <div class="form-field">
                <label>สรุปความสำคัญและเหตุผล <span class="required">*</span></label>
                <div class="field-value {'empty-field' if not background else ''}" style="min-height: 80px;">{background or '[อธิบายความสำคัญและเหตุผลของการวิจัย]'}</div>
            </div>
        </div>
    </div>
"""

    def _generate_section_7(self, form_data: Dict) -> str:
        """Section 7: Objectives"""
        primary_obj = form_data.get('primary_objective', '')
        secondary_obj = form_data.get('secondary_objectives', '')

        return f"""
    <div class="section">
        <div class="section-number">7. วัตถุประสงค์ (Objectives)</div>

        <div class="section-title">7.1 วัตถุประสงค์หลัก</div>
        <div class="form-row full">
            <div class="form-field">
                <div class="field-value {'empty-field' if not primary_obj else ''}" style="min-height: 60px;">{primary_obj or '[ระบุวัตถุประสงค์หลัก]'}</div>
            </div>
        </div>

        <div class="section-title">7.2 วัตถุประสงค์รอง</div>
        <div class="form-row full">
            <div class="form-field">
                <div class="field-value" style="min-height: 60px;">{secondary_obj or '[ไม่ระบุ]'}</div>
            </div>
        </div>
    </div>
"""

    def _generate_section_8(self, form_data: Dict) -> str:
        """Section 8: Expected Benefits"""
        benefits = form_data.get('expected_benefits', '')

        return f"""
    <div class="section">
        <div class="section-number">8. ประโยชน์ที่คาดว่าจะได้ (Expected Benefits)</div>

        <div class="form-row full">
            <div class="form-field">
                <div class="field-value {'empty-field' if not benefits else ''}" style="min-height: 60px;">{benefits or '[อธิบายประโยชน์ที่จะได้รับ]'}</div>
            </div>
        </div>
    </div>
"""

    def _generate_section_9(self, form_data: Dict) -> str:
        """Section 9: Literature Review"""
        literature = form_data.get('literature_review', '')

        return f"""
    <div class="section">
        <div class="section-number">9. การรวบรวมรายงาน (Literature Review)</div>

        <div class="form-row full">
            <div class="form-field">
                <div class="field-value {'empty-field' if not literature else ''}" style="min-height: 80px;">{literature or '[ระบุการศึกษาที่คล้ายกัน]'}</div>
            </div>
        </div>
    </div>
"""

    def _generate_section_10(self, form_data: Dict) -> str:
        """Section 10: Study Design"""
        study_design = form_data.get('study_design', '')

        return f"""
    <div class="section">
        <div class="section-number">10. รูปแบบการวิจัย (Study Design)</div>

        <div class="form-row full">
            <div class="form-field">
                <label>เลือกรูปแบบการวิจัย <span class="required">*</span></label>
                <div class="field-value {'empty-field' if not study_design else ''}">{study_design or '[เลือกรูปแบบการวิจัย]'}</div>
            </div>
        </div>
    </div>
"""

    def _generate_section_11(self, form_data: Dict) -> str:
        """Section 11: Study Population"""
        target_pop = form_data.get('target_population', '')
        sample_size = form_data.get('sample_size', '')
        recruitment = form_data.get('recruitment_process', '')
        inclusion = form_data.get('inclusion_criteria', '')
        exclusion = form_data.get('exclusion_criteria', '')

        return f"""
    <div class="section">
        <div class="section-number">11. ลักษณะตัวอย่าง (Study Population)</div>

        <div class="section-title">11.1 ประชากรเป้าหมาย</div>
        <div class="form-row full">
            <div class="form-field">
                <div class="field-value {'empty-field' if not target_pop else ''}" style="min-height: 60px;">{target_pop or '[อธิบายประชากรเป้าหมาย]'}</div>
            </div>
        </div>

        <div class="section-title">11.2 ขนาดตัวอย่าง</div>
        <div class="form-row full">
            <div class="form-field">
                <div class="field-value {'empty-field' if not sample_size else ''}">{sample_size or '[จำนวนผู้เข้าร่วม]'}</div>
            </div>
        </div>

        <div class="section-title">11.3 วิธีการสรรหา</div>
        <div class="form-row full">
            <div class="form-field">
                <div class="field-value {'empty-field' if not recruitment else ''}" style="min-height: 60px;">{recruitment or '[อธิบายวิธีการ]'}</div>
            </div>
        </div>

        <div class="section-title">11.4 เกณฑ์การคัดเข้า</div>
        <div class="form-row full">
            <div class="form-field">
                <div class="field-value {'empty-field' if not inclusion else ''}" style="min-height: 60px;">{inclusion or '[ระบุเกณฑ์]'}</div>
            </div>
        </div>

        <div class="section-title">11.5 เกณฑ์การคัดออก</div>
        <div class="form-row full">
            <div class="form-field">
                <div class="field-value {'empty-field' if not exclusion else ''}" style="min-height: 60px;">{exclusion or '[ระบุเกณฑ์]'}</div>
            </div>
        </div>
    </div>
"""

    def _generate_section_12(self, form_data: Dict) -> str:
        """Section 12: Research Methodology"""
        procedures = form_data.get('study_procedures', '')
        outcomes = form_data.get('outcome_measurements', '')
        stats = form_data.get('statistical_analysis', '')

        return f"""
    <div class="section">
        <div class="section-number">12. ระเบียบวิธีวิจัย (Research Methodology)</div>

        <div class="section-title">12.1 ขั้นตอนการวิจัย</div>
        <div class="form-row full">
            <div class="form-field">
                <div class="field-value {'empty-field' if not procedures else ''}" style="min-height: 80px;">{procedures or '[อธิบายขั้นตอน]'}</div>
            </div>
        </div>

        <div class="section-title">12.2 การวัดผล</div>
        <div class="form-row full">
            <div class="form-field">
                <div class="field-value {'empty-field' if not outcomes else ''}" style="min-height: 80px;">{outcomes or '[ระบุตัวแปรที่จะวัด]'}</div>
            </div>
        </div>

        <div class="section-title">12.3 การวิเคราะห์ทางสถิติ</div>
        <div class="form-row full">
            <div class="form-field">
                <div class="field-value {'empty-field' if not stats else ''}" style="min-height: 60px;">{stats or '[ระบุวิธีการวิเคราะห์]'}</div>
            </div>
        </div>
    </div>
"""

    def _generate_section_14(self, form_data: Dict) -> str:
        """Section 14: Ethical Considerations"""
        consent = form_data.get('informed_consent_process', '')
        risks = form_data.get('foreseeable_risks', '')
        confidentiality = form_data.get('confidentiality', '')

        return f"""
    <div class="section">
        <div class="section-number">14. ข้อพิจารณาด้านจริยธรรม (Ethical Considerations)</div>

        <div class="section-title">14.1 กระบวนการขอความยินยอม</div>
        <div class="form-row full">
            <div class="form-field">
                <div class="field-value {'empty-field' if not consent else ''}" style="min-height: 60px;">{consent or '[อธิบายกระบวนการ]'}</div>
            </div>
        </div>

        <div class="section-title">14.3 ความเสี่ยง</div>
        <div class="form-row full">
            <div class="form-field">
                <div class="field-value {'empty-field' if not risks else ''}" style="min-height: 60px;">{risks or '[ระบุความเสี่ยง]'}</div>
            </div>
        </div>

        <div class="section-title">14.6 การรักษาความลับ</div>
        <div class="form-row full">
            <div class="form-field">
                <div class="field-value {'empty-field' if not confidentiality else ''}" style="min-height: 60px;">{confidentiality or '[อธิบายวิธีการ]'}</div>
            </div>
        </div>
    </div>
"""

    def _generate_section_17(self, form_data: Dict) -> str:
        """Section 17: Research Budget"""
        funding = form_data.get('funding_source', '')
        budget = form_data.get('budget_amount', '')

        return f"""
    <div class="section">
        <div class="section-number">17. งบประมาณในการวิจัย (Research Budget)</div>

        <div class="form-row">
            <div class="form-field">
                <label>แหล่งทุน</label>
                <div class="field-value">{funding or '[ไม่ระบุ]'}</div>
            </div>

            <div class="form-field">
                <label>จำนวนเงิน (บาท)</label>
                <div class="field-value">{budget or '[ไม่ระบุ]'}</div>
            </div>
        </div>
    </div>
"""

    def _generate_footer(self) -> str:
        """Generate document footer"""
        return """
    <div class="page-footer">
        <p>Generated using EC-MFU AI Document Generator | AP 02/2026</p>
        <p>Version: 1.0.0</p>
    </div>
</div>
"""

    def identify_missing_fields(self, form_data: Dict) -> List[Dict[str, Any]]:
        """
        Identify fields with missing or incomplete data

        Returns:
        - List of missing field objects with metadata
        """

        required_fields = [
            {'id': 'project_title_th', 'label': 'ชื่อโครงการ (ไทย)', 'section': 1},
            {'id': 'project_title_en', 'label': 'Project Title (English)', 'section': 1},
            {'id': 'field_of_study', 'label': 'สาขาวิชา', 'section': 2},
            {'id': 'principal_investigator_title', 'label': 'ผู้วิจัยหลัก', 'section': 3},
            {'id': 'principal_investigator_email', 'label': 'อีเมล PI', 'section': 3},
            {'id': 'start_month', 'label': 'เดือนเริ่ม', 'section': 4},
            {'id': 'end_month', 'label': 'เดือนสิ้นสุด', 'section': 4},
            {'id': 'study_site_description', 'label': 'สถานที่ทำการวิจัย', 'section': 5},
            {'id': 'background_significance', 'label': 'ความสำคัญ', 'section': 6},
            {'id': 'primary_objective', 'label': 'วัตถุประสงค์หลัก', 'section': 7},
            {'id': 'expected_benefits', 'label': 'ประโยชน์', 'section': 8},
            {'id': 'study_design', 'label': 'รูปแบบการวิจัย', 'section': 10},
        ]

        missing = []
        for field_def in required_fields:
            field_id = field_def['id']
            value = form_data.get(field_id, '')

            if not value or (isinstance(value, str) and value.strip() == ''):
                missing.append({
                    'field_id': field_id,
                    'label': field_def['label'],
                    'section': field_def['section'],
                    'severity': 'required'
                })

        return missing


# Helper function to get generator
def get_ap02_generator():
    """Get AP02 document generator instance"""
    return AP02DocumentGenerator()
