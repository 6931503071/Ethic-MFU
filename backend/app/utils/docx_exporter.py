"""
DOCX Exporter Module
Generates DOCX files with color-coded fields from analyzed documents
"""

import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# Import Thai font fix
try:
    from app.utils.thai_font_fix import fix_thai_text, enhance_docx_with_thai_fix
except ImportError:
    def fix_thai_text(text):
        return text
    def enhance_docx_with_thai_fix(doc, data):
        return doc


def create_docx(data: Dict[str, Any], template_config: Optional[Dict] = None) -> str:
    """
    Create DOCX file from analysis results with color-coded fields

    Parameters:
    - data: Response data with analysis, prototypes, metadata
    - template_config: Optional AP02 template configuration

    Returns:
    - Path to generated DOCX file
    """

    try:
        doc = Document()

        # Set default font to TH Sarabun New
        try:
            style = doc.styles['Normal']
            style.font.name = 'TH Sarabun New'
            style.font.size = Pt(16)

            # Set font for all styles
            for style_name in ['Title', 'Heading 1', 'Heading 2', 'Heading 3', 'Subtitle']:
                try:
                    s = doc.styles[style_name]
                    s.font.name = 'TH Sarabun New'
                except:
                    pass
        except Exception as e:
            print(f"Warning: Could not set Normal style font: {e}")

        # Add header
        _add_header(doc, data)

        # Add analysis section
        _add_analysis_section(doc, data)

        # Add prototypes section
        _add_prototypes_section(doc, data)

        # Set document margins (AP02 standard)
        sections = doc.sections
        for section in sections:
            section.top_margin = Cm(2.54)      # 25.4 mm
            section.bottom_margin = Cm(2.0)    # 20 mm
            section.left_margin = Cm(2.49)     # 24.9 mm
            section.right_margin = Cm(2.49)    # 24.9 mm

        # Apply Thai font fixes
        try:
            doc = enhance_docx_with_thai_fix(doc, data)
        except Exception as e:
            print(f"Warning: Could not apply Thai font fixes: {e}")

        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        doc.save(temp_file.name)
        temp_file.close()

        return temp_file.name

    except Exception as e:
        print(f"Error creating DOCX: {e}")
        import traceback
        traceback.print_exc()
        raise


def _add_header(doc: Document, data: Dict[str, Any]) -> None:
    """Add document header with title and metadata"""

    analysis = data.get('analysis', {})
    metadata = data.get('metadata', {})

    # Title
    title = doc.add_heading('📄 AI Document Generator Output', level=1)
    title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    # Document type and info
    info = doc.add_paragraph()
    info.add_run(f"Document Type: ").bold = True
    info.add_run(f"{analysis.get('document_type', 'Unknown')}\n")

    info.add_run(f"Language: ").bold = True
    lang_map = {'en': 'English', 'th': 'Thai', 'both': 'English & Thai'}
    info.add_run(f"{lang_map.get(analysis.get('language', 'en'), 'Unknown')}\n")

    info.add_run(f"File: ").bold = True
    info.add_run(f"{metadata.get('file_name', 'Unknown')}\n")

    info.add_run(f"Word Count: ").bold = True
    info.add_run(f"{analysis.get('word_count', 0)} words\n")

    doc.add_paragraph()  # Spacer


def _add_analysis_section(doc: Document, data: Dict[str, Any]) -> None:
    """Add document analysis results with color-coded fields"""

    analysis = data.get('analysis', {})

    doc.add_heading('📊 Document Analysis', level=2)

    # Errors section (if any)
    errors = analysis.get('errors', [])
    if errors:
        doc.add_heading('⚠️ Issues Found', level=3)
        for error in errors:
            p = doc.add_paragraph(error, style='List Bullet')

    # Missing fields section with color coding
    missing_fields = analysis.get('missing_fields', [])
    if missing_fields:
        doc.add_heading('🔴 Missing Required Fields', level=3)

        for field in missing_fields:
            # Add with red color and strikethrough for placeholders
            p = doc.add_paragraph()
            run = p.add_run(f"• {field}")
            run.font.color.rgb = RGBColor(220, 38, 38)  # Red
            run.font.bold = True

    # Field metadata with severity colors
    field_metadata = analysis.get('field_metadata', [])
    if field_metadata:
        doc.add_heading('📋 Field Status Overview', level=3)

        required_fields = [f for f in field_metadata if f.get('severity') == 'required']
        ambiguous_fields = [f for f in field_metadata if f.get('severity') == 'ambiguous']
        optional_fields = [f for f in field_metadata if f.get('severity') == 'optional']

        # Required fields (RED)
        if required_fields:
            doc.add_paragraph('Required Fields (Must fill):', style='List Heading')
            for field in required_fields[:5]:  # Show top 5
                p = doc.add_paragraph(f"{field.get('label', 'Unknown')} (Page {field.get('page', '?')})",
                                     style='List Bullet')
                run_status = p.add_run(' - Missing')
                run_status.font.color.rgb = RGBColor(220, 38, 38)  # Red

        # Ambiguous fields (YELLOW/ORANGE)
        if ambiguous_fields:
            doc.add_paragraph('Ambiguous Fields (Review needed):', style='List Heading')
            for field in ambiguous_fields[:5]:  # Show top 5
                p = doc.add_paragraph(f"{field.get('label', 'Unknown')} (Page {field.get('page', '?')}, Confidence: {field.get('confidence', 0)}%)",
                                     style='List Bullet')
                run_status = p.add_run(' - Review recommended')
                run_status.font.color.rgb = RGBColor(217, 119, 6)  # Orange/Yellow

        # Optional fields (GRAY)
        if optional_fields:
            doc.add_paragraph('Optional Fields (Nice to have):', style='List Heading')
            for field in optional_fields[:3]:  # Show top 3
                p = doc.add_paragraph(f"{field.get('label', 'Unknown')} (Page {field.get('page', '?')})",
                                     style='List Bullet')
                run_status = p.add_run(' - Optional')
                run_status.font.color.rgb = RGBColor(156, 163, 175)  # Gray

    doc.add_paragraph()  # Spacer


def _add_prototypes_section(doc: Document, data: Dict[str, Any]) -> None:
    """Add prototype documents with color-coded sections"""

    prototypes = data.get('prototypes', [])
    analysis = data.get('analysis', {})

    doc.add_heading('📝 Generated Document Prototypes', level=2)

    for idx, proto in enumerate(prototypes):
        # Prototype header
        proto_heading = doc.add_heading(f"Variant {idx + 1}: {proto.get('name', 'Prototype')}", level=3)

        # Style info
        description = proto.get('description', '')
        if description:
            doc.add_paragraph(description, style='Intense Quote')

        # Content with field highlighting
        content = proto.get('content', 'No content available')

        # Color-code placeholders in content
        _add_colored_content(doc, content, analysis.get('field_metadata', []))

        # Key sections
        highlighted = proto.get('highlighted_sections', [])
        if highlighted:
            doc.add_paragraph('Key Sections:', style='List Heading')
            for section in highlighted:
                doc.add_paragraph(section, style='List Bullet')

        # Add page break before next prototype (except last)
        if idx < len(prototypes) - 1:
            doc.add_page_break()


def _add_colored_content(doc: Document, content: str, field_metadata: List[Dict]) -> None:
    """
    Add content with color-coded fields based on severity

    - Red: Required fields (missing data)
    - Yellow/Orange: Ambiguous fields (low confidence)
    - Default: Regular text
    """

    import re

    # Build field mapping
    required_fields = {f.get('label', '').lower(): f
                      for f in field_metadata if f.get('severity') == 'required'}
    ambiguous_fields = {f.get('label', '').lower(): f
                       for f in field_metadata if f.get('severity') == 'ambiguous'}

    # Split content into lines and process
    lines = content.split('\n')
    para = None

    for line in lines:
        if not line.strip():
            if para:
                doc.add_paragraph()
                para = None
            continue

        # Create new paragraph for this line
        para = doc.add_paragraph()

        # Check if line contains placeholder markers
        if '[PLEASE' in line or '[TODO' in line:
            # This is a required field - RED
            run = para.add_run(line)
            run.font.color.rgb = RGBColor(220, 38, 38)  # Red
            run.font.bold = True
        else:
            # Check for ambiguous markers or low-confidence patterns
            is_ambiguous = any(marker in line.lower() for marker in ['unclear', '?', 'ambiguous', 'possibly'])

            if is_ambiguous:
                # Ambiguous field - YELLOW/ORANGE
                run = para.add_run(line)
                run.font.color.rgb = RGBColor(217, 119, 6)  # Orange/Yellow
            else:
                # Normal text
                run = para.add_run(line)
                run.font.color.rgb = RGBColor(31, 41, 55)  # Dark gray


def add_color_to_text(paragraph, text: str, color_rgb: tuple) -> None:
    """Helper to add colored text to paragraph"""
    run = paragraph.add_run(text)
    run.font.color.rgb = RGBColor(*color_rgb)
    return run
