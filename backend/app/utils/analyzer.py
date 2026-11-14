"""
Document Analyzer Module
Analyzes document content and provides feedback
"""

import re
from typing import List, Dict, Any


def analyze_document(text: str, document_type: str, language: str = 'en') -> Dict[str, Any]:
    """
    Analyze document and extract metadata

    Parameters:
    - text: Document text
    - document_type: Type of document (research_proposal, ethics_submission, etc.)
    - language: Output language (en, th, both)

    Returns:
    - Dictionary with analysis results including field metadata
    """

    analysis = {
        "document_type": map_document_type(document_type),
        "language": detect_language(text),
        "purpose": get_document_purpose(document_type),
        "status": "Complete",
        "word_count": len(text.split()),
        "page_estimate": len(text.split()) // 250,  # Rough estimate
        "errors": [],
        "warnings": [],
        "missing_fields": []
    }

    # Detect errors in the document
    analysis["errors"] = detect_errors(text, language)

    # Detect warnings
    analysis["warnings"] = detect_warnings(text, document_type, language)

    # Detect missing fields (original simple version)
    analysis["missing_fields"] = detect_missing_fields(text, document_type)

    # Create detailed field metadata with severity levels
    try:
        analysis["field_metadata"] = create_field_metadata(text, document_type, analysis)
    except Exception as e:
        # Fallback: create minimal field metadata
        print(f"Warning: Could not create detailed field metadata: {e}")
        analysis["field_metadata"] = []

    return analysis


def map_document_type(category: str) -> str:
    """Map category to friendly document type"""
    mapping = {
        "research_proposal": "Research Proposal (AP 02/2026)",
        "ethics_submission": "Ethics Submission Document",
        "general": "General Document",
        "administrative": "Administrative Document",
        "participant_info": "Participant Information Sheet",
        "consent_form": "Research Consent Form"
    }
    return mapping.get(category, "Document")


def get_document_purpose(category: str) -> str:
    """Get document purpose based on category"""
    purposes = {
        "research_proposal": "Research Ethics Committee Submission",
        "ethics_submission": "Research Ethics Submission",
        "general": "General Administrative Use",
        "administrative": "Administrative Processing",
        "participant_info": "Participant Information",
        "consent_form": "Research Participant Consent"
    }
    return purposes.get(category, "Unknown")


def detect_language(text: str) -> str:
    """
    Detect if document is English or Thai

    Simple heuristic based on character ranges
    """

    # Thai character range: U+0E00 - U+0E7F
    thai_chars = sum(1 for c in text if '฀' <= c <= '๿')

    # English letters
    english_chars = sum(1 for c in text if c.isalpha() and ord(c) < 128)

    # If more Thai characters, it's Thai
    if thai_chars > english_chars:
        return "th"
    else:
        return "en"


def detect_errors(text: str, language: str = 'en') -> List[str]:
    """
    Detect common errors in document

    Checks for:
    - Spelling issues
    - Missing punctuation
    - Inconsistent formatting
    - Placeholder text
    """

    errors = []

    # Check for [PLACEHOLDER] text
    placeholders = re.findall(r'\[PLEASE.*?\]', text, re.IGNORECASE)
    if placeholders:
        errors.append(f"Found {len(placeholders)} unfilled placeholders")

    # Check for [TODO]
    if '[TODO]' in text or '[todo]' in text:
        errors.append("Document contains [TODO] markers")

    # Check for consecutive uppercase words (potential typos)
    uppercase_sequences = re.findall(r'\b[A-Z]{2,}\b', text)
    if len(uppercase_sequences) > 10:
        errors.append("Multiple consecutive uppercase words detected (possible formatting issue)")

    # Check for double spaces (common typo)
    if '  ' in text:
        errors.append("Document contains multiple consecutive spaces")

    # Check for common misspellings (language-specific)
    if language == 'en':
        common_errors_en = {
            r'\bthe the\b': 'Duplicate word "the"',
            r'\brecieve\b': 'Misspelling: "recieve" should be "receive"',
            r'\bwich\b': 'Misspelling: "wich" should be "which"',
            r'\baccomodate\b': 'Misspelling: "accomodate" should be "accommodate"'
        }

        for pattern, error_msg in common_errors_en.items():
            if re.search(pattern, text, re.IGNORECASE):
                errors.append(error_msg)

    return errors[:5]  # Return max 5 errors


def detect_warnings(text: str, document_type: str, language: str = 'en') -> List[str]:
    """
    Detect warnings and suggestions

    Checks for:
    - Missing sections
    - Very short paragraphs
    - Inconsistent terminology
    """

    warnings = []

    # Check if document is too short
    word_count = len(text.split())
    if word_count < 100:
        warnings.append("Document is very short (less than 100 words)")

    # Check for missing key sections based on document type
    if document_type == "research_proposal":
        required_sections = {
            "background": r'(background|introduction|literature)',
            "objective": r'(objective|aim|goal)',
            "method": r'(method|procedure|approach)',
            "expected": r'(expected|expected|anticipated)',
            "reference": r'(reference|citation)'
        }

        for section_name, pattern in required_sections.items():
            if not re.search(pattern, text, re.IGNORECASE):
                warnings.append(f"Possibly missing '{section_name}' section")

    # Check for very long paragraphs (>500 words)
    paragraphs = text.split('\n\n')
    long_paras = [p for p in paragraphs if len(p.split()) > 500]
    if long_paras:
        warnings.append(f"{len(long_paras)} very long paragraphs detected (consider breaking them up)")

    return warnings[:5]  # Return max 5 warnings


def detect_missing_fields(text: str, document_type: str) -> List[str]:
    """
    Detect fields that must be filled manually

    Returns list of placeholder suggestions based on document type
    """

    missing_fields = []

    # Check what's already in the text
    has_researcher_name = bool(re.search(r'(Dr\.|Prof\.|Researcher|PI)', text, re.IGNORECASE))
    has_title = bool(re.search(r'(research title|project title|title:)', text, re.IGNORECASE))
    has_date = bool(re.search(r'\d{1,2}/\d{1,2}/\d{4}', text))
    has_institution = bool(re.search(r'(university|institute|faculty|department)', text, re.IGNORECASE))

    # Add missing field placeholders
    if not has_researcher_name:
        missing_fields.append("[PLEASE ENTER RESEARCHER/PI NAME]")
        missing_fields.append("[PLEASE ENTER RESEARCHER AFFILIATION]")

    if not has_title:
        missing_fields.append("[PLEASE ENTER RESEARCH TITLE]")

    if not has_date:
        missing_fields.append("[PLEASE ENTER PROJECT DATES]")
        missing_fields.append("[PLEASE ENTER SUBMISSION DATE]")

    if not has_institution:
        missing_fields.append("[PLEASE ENTER INSTITUTION NAME]")

    # Document-specific fields
    if document_type == "research_proposal":
        missing_fields.append("[PLEASE ENTER ETHICS APPROVAL NUMBER]")
        missing_fields.append("[PLEASE ENTER BUDGET DETAILS]")
        missing_fields.append("[PLEASE ENTER EXPECTED OUTCOMES]")

    elif document_type == "ethics_submission":
        missing_fields.append("[PLEASE CONFIRM ETHICS COMMITTEE]")
        missing_fields.append("[PLEASE ENTER RISK ASSESSMENT]")
        missing_fields.append("[PLEASE ENTER MITIGATION STRATEGIES]")

    return missing_fields[:5]  # Return max 5 missing fields


def create_field_metadata(text: str, document_type: str, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Create detailed field metadata with severity levels and AI confidence

    Returns list of field objects with:
    - id, label, page, severity (required/ambiguous/optional)
    - confidence (AI confidence score 0-100)
    """

    field_metadata = []
    page_number = 1

    # Define required fields for AP02
    required_fields_ap02 = [
        {"id": "title_th", "label": "Research Title (Thai)", "severity": "required"},
        {"id": "title_en", "label": "Research Title (English)", "severity": "required"},
        {"id": "field_of_study", "label": "Field of Study", "severity": "required"},
        {"id": "researcher_name", "label": "Researcher/PI Name", "severity": "required"},
        {"id": "institution", "label": "Institution Name", "severity": "required"},
        {"id": "ethics_approval", "label": "Ethics Approval Number", "severity": "required"},
        {"id": "project_dates", "label": "Project Dates", "severity": "required"},
    ]

    optional_fields_ap02 = [
        {"id": "budget", "label": "Budget Details", "severity": "optional"},
        {"id": "location", "label": "Research Location", "severity": "optional"},
        {"id": "outcomes", "label": "Expected Outcomes", "severity": "optional"},
    ]

    # Check which required fields are present
    for field in required_fields_ap02:
        field_id = field['id']
        label = field['label']

        # Check if field content exists in text
        field_found = False
        confidence = 0

        if field_id in ['title_th', 'title_en']:
            if re.search(r'(research title|project title|title:)', text, re.IGNORECASE):
                field_found = True
                confidence = 85
        elif field_id == 'field_of_study':
            if re.search(r'(medicine|dentistry|public health|engineering|science)', text, re.IGNORECASE):
                field_found = True
                confidence = 90
        elif field_id == 'researcher_name':
            if re.search(r'(Dr\.|Prof\.|Researcher|PI|author)', text, re.IGNORECASE):
                field_found = True
                confidence = 75
        elif field_id == 'institution':
            if re.search(r'(university|institute|faculty|department|hospital)', text, re.IGNORECASE):
                field_found = True
                confidence = 88
        elif field_id == 'ethics_approval':
            if re.search(r'(ethics|approval|number|code|ec-)', text, re.IGNORECASE):
                field_found = True
                confidence = 70
        elif field_id == 'project_dates':
            if re.search(r'\d{1,2}/\d{1,2}/\d{4}', text):
                field_found = True
                confidence = 92

        # Determine severity based on presence and confidence
        if field_found:
            if confidence < 80:
                severity = "ambiguous"
            else:
                severity = "optional"  # Found, so not required
        else:
            severity = "required"  # Not found, so required

        field_metadata.append({
            "id": field_id,
            "label": label,
            "page": page_number,
            "severity": severity,
            "confidence": confidence,
            "status": "filled" if field_found else "empty"
        })

        # Add optional fields
        if page_number > 1:
            page_number += 1

    # Add optional fields
    for field in optional_fields_ap02:
        field_metadata.append({
            "id": field['id'],
            "label": field['label'],
            "page": page_number,
            "severity": "optional",
            "confidence": 50,
            "status": "empty"
        })

    return field_metadata
