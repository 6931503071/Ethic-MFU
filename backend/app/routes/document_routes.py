"""
AP02 Document Generation API Routes
Endpoints for generating and manipulating AP02 documents
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from app.utils.ap02_document_generator import get_ap02_generator

router = APIRouter(prefix="/api/document", tags=["document"])


# ════════════════════════════════════════════════════
# PYDANTIC MODELS
# ════════════════════════════════════════════════════

class FormData(BaseModel):
    """Form data for document generation"""
    data: Dict[str, Any]


class DocumentRequest(BaseModel):
    """Request for document generation/manipulation"""
    form_version: str = "AP 02/2026"
    language: str = "en"
    form_data: Dict[str, Any]


# ════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════

@router.post("/generate/html")
async def generate_ap02_html(request: DocumentRequest):
    """
    Generate AP02 document as HTML

    Parameters:
    - form_data: Dictionary of form field values

    Returns:
    - HTML document as string
    """
    try:
        generator = get_ap02_generator()
        html_content = generator.generate_html(request.form_data)

        return {
            "status": "success",
            "data": {
                "format": "html",
                "content": html_content,
                "form_version": request.form_version
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/identify-missing-fields")
async def identify_missing_fields(request: DocumentRequest):
    """
    Identify missing or incomplete fields in the form

    Returns:
    - List of missing fields with metadata
    """
    try:
        generator = get_ap02_generator()
        missing_fields = generator.identify_missing_fields(request.form_data)

        return {
            "status": "success",
            "missing_count": len(missing_fields),
            "missing_fields": missing_fields,
            "summary": {
                "critical": len([f for f in missing_fields if f['severity'] == 'required']),
                "warnings": len([f for f in missing_fields if f['severity'] == 'warning'])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview")
async def preview_document(request: DocumentRequest):
    """
    Generate document preview with missing field highlights

    Returns:
    - HTML preview with visual indicators for missing data
    """
    try:
        generator = get_ap02_generator()
        html_content = generator.generate_html(request.form_data)
        missing_fields = generator.identify_missing_fields(request.form_data)

        preview = {
            "status": "success",
            "html": html_content,
            "missing_fields": missing_fields,
            "completion_status": {
                "total_required": len([f for f in missing_fields]),
                "filled": sum(1 for k, v in request.form_data.items() if v),
                "completion_percentage": (sum(1 for k, v in request.form_data.items() if v) / len(request.form_data) * 100) if request.form_data else 0
            },
            "ready_for_export": len(missing_fields) == 0
        }

        return preview
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-for-export")
async def validate_for_export(request: DocumentRequest):
    """
    Validate document is ready for export

    Returns:
    - Validation status and any blocking issues
    """
    try:
        generator = get_ap02_generator()
        missing_fields = generator.identify_missing_fields(request.form_data)

        critical_missing = [f for f in missing_fields if f['severity'] == 'required']

        return {
            "status": "success",
            "ready_for_export": len(critical_missing) == 0,
            "blocking_issues": critical_missing,
            "warnings": [f for f in missing_fields if f['severity'] == 'warning'],
            "validation_message": (
                "Document is ready for export" if len(critical_missing) == 0
                else f"{len(critical_missing)} required fields are missing"
            )
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-editable-fields")
async def extract_editable_fields(request: DocumentRequest):
    """
    Extract fields from document that can be edited

    Returns:
    - List of editable field locations in the document
    """
    try:
        # This would return coordinates/references for clickable sections
        editable_sections = [
            {
                "section": 1,
                "fields": [
                    {"field_id": "project_title_th", "label": "Thai Title", "editable": True},
                    {"field_id": "project_title_en", "label": "English Title", "editable": True}
                ]
            },
            {
                "section": 2,
                "fields": [
                    {"field_id": "field_of_study", "label": "Field of Study", "editable": True},
                    {"field_id": "field_subspecialty", "label": "Sub-specialty", "editable": True}
                ]
            },
            # ... more sections
        ]

        return {
            "status": "success",
            "editable_sections": editable_sections,
            "total_editable_fields": sum(len(s["fields"]) for s in editable_sections)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/field-update")
async def update_field_in_document(
    field_id: str,
    new_value: str,
    request: DocumentRequest
):
    """
    Update a specific field and regenerate document

    Parameters:
    - field_id: The field to update
    - new_value: The new value

    Returns:
    - Updated document HTML
    """
    try:
        # Update form data
        request.form_data[field_id] = new_value

        # Regenerate document
        generator = get_ap02_generator()
        html_content = generator.generate_html(request.form_data)

        return {
            "status": "success",
            "field_id": field_id,
            "new_value": new_value,
            "html": html_content,
            "message": f"Field '{field_id}' updated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-update")
async def batch_update_fields(request: DocumentRequest):
    """
    Update multiple fields at once

    Parameters:
    - form_data: Dictionary of field_id -> new_value mappings

    Returns:
    - Updated document HTML
    """
    try:
        generator = get_ap02_generator()
        html_content = generator.generate_html(request.form_data)

        return {
            "status": "success",
            "fields_updated": len(request.form_data),
            "html": html_content,
            "message": f"Updated {len(request.form_data)} fields"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/get-section")
async def get_document_section(
    section_id: int,
    request: DocumentRequest
):
    """
    Get a specific section of the document

    Returns:
    - HTML for that section only
    """
    try:
        generator = get_ap02_generator()
        full_html = generator.generate_html(request.form_data)

        # Extract section (this would be more sophisticated in reality)
        return {
            "status": "success",
            "section_id": section_id,
            "html": full_html,  # Simplified - in real implementation would extract just that section
            "message": f"Retrieved section {section_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/get-statistics")
async def get_document_statistics(request: DocumentRequest):
    """
    Get statistics about the document

    Returns:
    - Word count, field count, completion percentage, etc.
    """
    try:
        generator = get_ap02_generator()
        missing_fields = generator.identify_missing_fields(request.form_data)

        filled_fields = sum(1 for k, v in request.form_data.items() if v)
        total_fields = len(request.form_data)

        return {
            "status": "success",
            "statistics": {
                "total_fields": total_fields,
                "filled_fields": filled_fields,
                "empty_fields": total_fields - filled_fields,
                "completion_percentage": (filled_fields / total_fields * 100) if total_fields > 0 else 0,
                "missing_required_fields": len([f for f in missing_fields if f['severity'] == 'required']),
                "form_version": "AP 02/2026"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
