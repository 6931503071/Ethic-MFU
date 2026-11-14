"""
PDF Exporter Module
Generates PDF files from DOCX output
"""

import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
import subprocess
import os


def create_pdf(data: Dict[str, Any], docx_path: Optional[str] = None) -> str:
    """
    Create PDF file from DOCX or analysis data

    Parameters:
    - data: Response data with analysis and prototypes
    - docx_path: Optional path to pre-generated DOCX file

    Returns:
    - Path to generated PDF file
    """

    # If no DOCX provided, generate one first
    if not docx_path:
        from app.utils.docx_exporter import create_docx
        docx_path = create_docx(data)

    # Convert DOCX to PDF
    try:
        pdf_path = _convert_docx_to_pdf(docx_path)
        return pdf_path
    except Exception as e:
        # Fallback: Return DOCX if PDF conversion fails
        print(f"⚠️ PDF conversion failed: {e}. Returning DOCX instead.")
        return docx_path


def _convert_docx_to_pdf(docx_path: str) -> str:
    """
    Convert DOCX to PDF using available method

    Tries multiple approaches:
    1. LibreOffice (if available)
    2. pandoc (if available)
    3. Fallback: return DOCX path
    """

    pdf_path = docx_path.replace('.docx', '.pdf')

    # Try LibreOffice
    try:
        subprocess.run([
            'libreoffice', '--headless', '--convert-to', 'pdf',
            '--outdir', str(Path(docx_path).parent),
            docx_path
        ], check=True, timeout=30)

        if Path(pdf_path).exists():
            return pdf_path
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Try pandoc
    try:
        subprocess.run([
            'pandoc', docx_path, '-o', pdf_path
        ], check=True, timeout=30)

        if Path(pdf_path).exists():
            return pdf_path
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Fallback: Use docx2pdf if available
    try:
        from docx2pdf.convert import convert
        convert(docx_path, pdf_path)

        if Path(pdf_path).exists():
            return pdf_path
    except ImportError:
        pass

    # Ultimate fallback: Return original DOCX path
    # In production, you'd want to fail gracefully or use a different solution
    return docx_path
