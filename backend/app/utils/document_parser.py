"""
Document Parser Module
Handles extraction of text from different file formats
"""

import io
import re
from pathlib import Path


def parse_document(file_content: bytes, file_ext: str) -> str:
    """
    Parse document and extract text based on file type

    Parameters:
    - file_content: Binary file content
    - file_ext: File extension (.pdf, .docx, .txt)

    Returns:
    - Extracted text as string
    """

    if file_ext == '.txt':
        return parse_txt(file_content)
    elif file_ext == '.docx':
        return parse_docx(file_content)
    elif file_ext == '.pdf':
        return parse_pdf(file_content)
    else:
        raise ValueError(f"Unsupported file type: {file_ext}")


def parse_txt(file_content: bytes) -> str:
    """Extract text from TXT file"""
    try:
        # Try UTF-8 first
        return file_content.decode('utf-8')
    except UnicodeDecodeError:
        # Try other encodings
        try:
            return file_content.decode('latin-1')
        except:
            return file_content.decode('utf-16')


def parse_docx(file_content: bytes) -> str:
    """Extract text from DOCX file"""
    try:
        from docx import Document
        from io import BytesIO

        # Load DOCX from bytes
        doc = Document(BytesIO(file_content))

        # Extract all paragraphs
        text_content = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_content.append(para.text)

        # Extract from tables
        for table in doc.tables:
            for row in table.rows:
                row_text = ' | '.join(
                    cell.text for cell in row.cells
                )
                if row_text.strip():
                    text_content.append(row_text)

        return '\n'.join(text_content)

    except ImportError:
        raise ImportError("python-docx not installed. Install with: pip install python-docx")


def parse_pdf(file_content: bytes) -> str:
    """Extract text from PDF file"""
    try:
        try:
            # Try newer PyPDF2 version (4.x+)
            from PyPDF2 import PdfReader
            from io import BytesIO

            pdf_reader = PdfReader(BytesIO(file_content))

            text_content = []
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text and text.strip():
                    text_content.append(text)

            return '\n'.join(text_content) if text_content else "[PDF content not extracted]"

        except (ImportError, AttributeError):
            # Fallback to older PyPDF2 version (3.x)
            import PyPDF2
            from io import BytesIO

            pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))

            text_content = []
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text and text.strip():
                    text_content.append(text)

            return '\n'.join(text_content) if text_content else "[PDF content not extracted]"

    except Exception as e:
        print(f"Warning: PDF parsing failed: {e}")
        return "[Could not parse PDF - please use DOCX or TXT instead]"


def clean_text(text: str) -> str:
    """
    Clean extracted text

    Removes:
    - Extra whitespace
    - Special characters
    - Empty lines
    """

    # Remove multiple spaces
    text = re.sub(r' +', ' ', text)

    # Remove multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def extract_sections(text: str, language: str = 'en') -> dict:
    """
    Attempt to identify document sections

    Parameters:
    - text: Document text
    - language: en or th

    Returns:
    - Dictionary of identified sections
    """

    sections = {
        "title": "",
        "introduction": "",
        "methods": "",
        "results": "",
        "discussion": "",
        "conclusion": "",
        "references": "",
        "other": ""
    }

    # Simple heuristic: look for section headers
    lines = text.split('\n')
    current_section = "other"

    keywords = {
        "introduction": ["introduction", "background", "บทนำ"],
        "methods": ["method", "methodology", "procedure", "วิธี"],
        "results": ["result", "finding", "ผลลัพธ์"],
        "discussion": ["discussion", "implication", "การอภิปราย"],
        "conclusion": ["conclusion", "summary", "บทสรุป"],
        "references": ["reference", "bibliography", "อ้างอิง"]
    }

    for line in lines:
        line_lower = line.lower()

        for section_name, keywords_list in keywords.items():
            if any(kw in line_lower for kw in keywords_list):
                current_section = section_name
                break

        sections[current_section] += line + "\n"

    return sections
