"""
Thai Font Fix Module
Corrects Thai character encoding and font issues in DOCX exports
"""

def fix_thai_text(text: str) -> str:
    """
    Fix common Thai text encoding and display issues

    Fixes:
    - Zero-width characters
    - Misplaced tone marks
    - Vowel combining issues
    """

    if not text:
        return text

    # Thai character ranges
    THAI_CONSONANTS = 'ก-ฮ'
    THAI_VOWELS = 'ะ-ู'
    THAI_TONES = '่-๋'

    # Fix common encoding issues
    import re

    # Remove zero-width spaces and joiners that cause display issues
    text = text.replace('​', '')  # Zero-width space
    text = text.replace('‌', '')  # Zero-width non-joiner
    text = text.replace('‍', '')  # Zero-width joiner

    # Normalize vowel placement - ensure vowels come after consonants
    # Pattern: consonant + tone + vowel → consonant + vowel + tone
    pattern = r'([เแโไใ])([ะัจ])'
    text = re.sub(pattern, r'\2\1', text)

    # Ensure proper tone mark placement
    # Tone marks should come after the main vowel
    tone_patterns = [
        (r'([ัิึุู])([่้๊๋])', r'\1\2'),  # vowel + tone (correct)
        (r'([่้๊๋])([ัิึุู])', r'\2\1'),  # tone + vowel (wrong, fix it)
    ]

    for pattern, replacement in tone_patterns:
        text = re.sub(pattern, replacement, text)

    return text


def enhance_docx_with_thai_fix(doc, analysis_data):
    """
    Enhance DOCX document with proper Thai font rendering

    Parameters:
    - doc: python-docx Document object
    - analysis_data: Analysis results with text content
    """

    from docx.shared import Pt
    from docx.oxml.shared import OxmlElement

    # Set font family for all paragraphs
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            # Set font to TH Sarabun New with fallback
            run.font.name = 'TH Sarabun New'

            # Add font compatibility settings
            try:
                # Add rFonts with hint for Asian fonts
                rFonts = OxmlElement('w:rFonts')
                rFonts.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ascii', 'TH Sarabun New')
                rFonts.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}hAnsi', 'TH Sarabun New')
                rFonts.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}cs', 'TH Sarabun New')

                run._element.get_or_add_rPr().append(rFonts)
            except:
                pass

            # Fix text content if it contains Thai
            if any('฀' <= c <= '๿' for c in run.text):
                fixed_text = fix_thai_text(run.text)
                if fixed_text != run.text:
                    run.text = fixed_text

    # Set font for tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.name = 'TH Sarabun New'

                        # Fix text
                        if any('฀' <= c <= '๿' for c in run.text):
                            fixed_text = fix_thai_text(run.text)
                            if fixed_text != run.text:
                                run.text = fixed_text

    return doc
