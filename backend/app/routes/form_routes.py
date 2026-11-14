"""
AP 02/2026 Form API Endpoints
Handles form schema retrieval and form-based document analysis
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from app.utils.form_schema import get_form_schema

router = APIRouter(prefix="/api/form", tags=["form"])


# ════════════════════════════════════════════════════
# PYDANTIC MODELS
# ════════════════════════════════════════════════════

class FormFieldValue(BaseModel):
    field_id: str
    value: Any
    notes: Optional[str] = None


class FormSubmission(BaseModel):
    form_version: str = "AP 02/2026"
    language: str = "en"
    fields: List[FormFieldValue]


# ════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════

@router.get("/schema/{language}")
async def get_form_schema_endpoint(language: str = "en"):
    """
    Get the complete AP 02/2026 form schema in specified language

    Parameters:
    - language: 'en' for English, 'th' for Thai

    Returns:
    - Complete form structure with all fields and sections
    """
    try:
        schema = get_form_schema()
        structure = schema.get_form_structure(language=language)
        return {
            "status": "success",
            "data": structure
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fields/required")
async def get_required_fields(language: str = "en"):
    """
    Get all required fields for AP 02/2026 form

    Returns:
    - List of required field definitions
    """
    try:
        schema = get_form_schema()
        required_fields = schema.get_required_fields()

        result = []
        for field in required_fields:
            result.append({
                "id": field.get("id"),
                "label": field.get("label", {}).get(language, field.get("label", {}).get("en")),
                "type": field.get("type"),
                "severity": field.get("severity")
            })

        return {
            "status": "success",
            "count": len(result),
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fields/by-severity/{severity}")
async def get_fields_by_severity(severity: str, language: str = "en"):
    """
    Get fields filtered by severity level

    Parameters:
    - severity: 'required', 'optional', or 'ambiguous'
    - language: 'en' or 'th'

    Returns:
    - List of fields matching the severity level
    """
    valid_severities = ["required", "optional", "ambiguous"]
    if severity not in valid_severities:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid severity. Use: {', '.join(valid_severities)}"
        )

    try:
        schema = get_form_schema()
        fields = schema.get_fields_by_severity(severity)

        result = []
        for field in fields:
            result.append({
                "id": field.get("id"),
                "label": field.get("label", {}).get(language, field.get("label", {}).get("en")),
                "type": field.get("type"),
                "severity": field.get("severity")
            })

        return {
            "status": "success",
            "severity": severity,
            "count": len(result),
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/field/{field_id}")
async def get_field_details(field_id: str, language: str = "en"):
    """
    Get details for a specific form field

    Parameters:
    - field_id: The unique field identifier
    - language: 'en' or 'th'

    Returns:
    - Field definition with options if applicable
    """
    try:
        schema = get_form_schema()
        field = schema.get_field_by_id(field_id)

        if not field:
            raise HTTPException(status_code=404, detail=f"Field '{field_id}' not found")

        response = {
            "id": field.get("id"),
            "label": field.get("label", {}).get(language, field.get("label", {}).get("en")),
            "type": field.get("type"),
            "required": field.get("required", False),
            "severity": field.get("severity", "optional")
        }

        # Add options if present
        if "options" in field:
            response["options"] = [
                {
                    "value": opt.get("value"),
                    "label": opt.get("label", {}).get(language, opt.get("label", {}).get("en"))
                }
                for opt in field.get("options", [])
            ]

        return {
            "status": "success",
            "data": response
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-field")
async def validate_field(field_id: str, value: Any):
    """
    Validate a field value

    Parameters:
    - field_id: The field to validate
    - value: The value to validate

    Returns:
    - Validation result with any error messages
    """
    try:
        schema = get_form_schema()
        is_valid, error_msg = schema.validate_field_value(field_id, value)

        return {
            "status": "success",
            "field_id": field_id,
            "is_valid": is_valid,
            "error": error_msg
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/empty-form")
async def get_empty_form():
    """
    Get an empty form data structure with all fields
    Useful for initializing a new form

    Returns:
    - Dictionary with all field IDs initialized to empty/null values
    """
    try:
        schema = get_form_schema()
        form_data = schema.generate_empty_form_data()

        return {
            "status": "success",
            "form_version": "AP 02/2026",
            "data": form_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sections")
async def get_form_sections(language: str = "en"):
    """
    Get all form sections with their field counts

    Parameters:
    - language: 'en' or 'th'

    Returns:
    - List of sections with metadata
    """
    try:
        schema = get_form_schema()
        sections = []

        for section in schema.sections:
            fields = section.get("fields", [])
            sections.append({
                "id": section.get("id"),
                "title": section.get("title", {}).get(language, section.get("title", {}).get("en")),
                "field_count": len(fields),
                "required_field_count": sum(1 for f in fields if f.get("required", False))
            })

        return {
            "status": "success",
            "total_sections": len(sections),
            "data": sections
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-submission")
async def validate_form_submission(submission: FormSubmission):
    """
    Validate a complete form submission

    Parameters:
    - submission: The form data to validate

    Returns:
    - Validation results with errors and warnings
    """
    try:
        schema = get_form_schema()
        errors = []
        warnings = []
        missing_required = []

        # Collect all field values
        submitted_fields = {fv.field_id: fv.value for fv in submission.fields}

        # Check all required fields
        for field in schema.get_required_fields():
            field_id = field.get("id")
            if field_id not in submitted_fields or not submitted_fields[field_id]:
                missing_required.append({
                    "field_id": field_id,
                    "label": field.get("label", {}).get(submission.language, ""),
                    "severity": "required"
                })

        # Validate each submitted field
        for field_id, value in submitted_fields.items():
            is_valid, error_msg = schema.validate_field_value(field_id, value)
            if not is_valid and error_msg:
                errors.append({
                    "field_id": field_id,
                    "error": error_msg
                })

        is_valid = len(errors) == 0 and len(missing_required) == 0

        return {
            "status": "success",
            "is_valid": is_valid,
            "errors": errors,
            "missing_required": missing_required,
            "warnings": warnings,
            "summary": {
                "total_errors": len(errors),
                "missing_required_fields": len(missing_required),
                "total_warnings": len(warnings)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/form-checklist/{language}")
async def get_form_checklist(language: str = "en"):
    """
    Get a checklist view of all form sections and their completion status

    Parameters:
    - language: 'en' or 'th'

    Returns:
    - Checklist format showing sections and required fields
    """
    try:
        schema = get_form_schema()
        checklist = []

        for section in schema.sections:
            section_item = {
                "id": section.get("id"),
                "title": section.get("title", {}).get(language, section.get("title", {}).get("en")),
                "fields": []
            }

            for field in section.get("fields", []):
                section_item["fields"].append({
                    "id": field.get("id"),
                    "label": field.get("label", {}).get(language, field.get("label", {}).get("en")),
                    "required": field.get("required", False),
                    "completed": False
                })

            checklist.append(section_item)

        return {
            "status": "success",
            "form_version": "AP 02/2026",
            "language": language,
            "data": checklist
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
