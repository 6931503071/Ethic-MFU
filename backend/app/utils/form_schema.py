"""
AP 02/2026 Form Schema Handler
Provides utilities to work with the research protocol proposal form
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class AP02FormSchema:
    """Handler for AP 02/2026 Research Protocol Proposal Form"""

    def __init__(self):
        """Load the form schema from JSON"""
        schema_path = Path(__file__).parent.parent / "schemas" / "ap02_form.json"
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)
        self.form_version = self.schema.get("form_version", "AP 02/2026")
        self.sections = self.schema.get("sections", [])

    def get_form_title(self, language: str = "en") -> str:
        """Get form title in specified language"""
        title = self.schema.get("title", {})
        return title.get(language, title.get("en", "Research Protocol Proposal Form"))

    def get_all_fields(self) -> List[Dict[str, Any]]:
        """Get all fields from all sections"""
        fields = []
        for section in self.sections:
            fields.extend(section.get("fields", []))
        return fields

    def get_required_fields(self) -> List[Dict[str, Any]]:
        """Get all required fields"""
        return [f for f in self.get_all_fields() if f.get("required", False)]

    def get_fields_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """Get fields by severity level (required, optional, ambiguous)"""
        return [f for f in self.get_all_fields() if f.get("severity") == severity]

    def get_section_by_id(self, section_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific section by ID"""
        for section in self.sections:
            if section.get("id") == section_id:
                return section
        return None

    def get_section_title(self, section_id: str, language: str = "en") -> str:
        """Get section title in specified language"""
        section = self.get_section_by_id(section_id)
        if section:
            title = section.get("title", {})
            return title.get(language, title.get("en", ""))
        return ""

    def get_field_by_id(self, field_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific field by ID"""
        for field in self.get_all_fields():
            if field.get("id") == field_id:
                return field
        return field

    def get_field_label(self, field_id: str, language: str = "en") -> str:
        """Get field label in specified language"""
        field = self.get_field_by_id(field_id)
        if field:
            label = field.get("label", {})
            if isinstance(label, dict):
                return label.get(language, label.get("en", ""))
            return str(label)
        return ""

    def validate_field_value(self, field_id: str, value: Any) -> tuple[bool, Optional[str]]:
        """
        Validate a field value against its schema
        Returns: (is_valid, error_message)
        """
        field = self.get_field_by_id(field_id)
        if not field:
            return False, "Field not found"

        # Check required
        if field.get("required", False) and not value:
            return False, "This field is required"

        # Type validation
        field_type = field.get("type", "text")

        if field_type == "email":
            if value and "@" not in str(value):
                return False, "Invalid email format"

        elif field_type == "number":
            try:
                float(value)
            except (ValueError, TypeError):
                return False, "Must be a number"

        elif field_type == "date":
            # Basic date validation (YYYY-MM-DD)
            if value:
                try:
                    from datetime import datetime
                    datetime.strptime(str(value), "%Y-%m-%d")
                except ValueError:
                    return False, "Invalid date format (use YYYY-MM-DD)"

        elif field_type == "select":
            options = field.get("options", [])
            valid_values = [opt["value"] for opt in options]
            if value and value not in valid_values:
                return False, f"Invalid selection. Choose from: {', '.join(valid_values)}"

        return True, None

    def get_form_structure(self, language: str = "en") -> Dict[str, Any]:
        """Get the complete form structure in a specific language"""
        structure = {
            "form_version": self.form_version,
            "form_title": self.get_form_title(language),
            "sections": []
        }

        for section in self.sections:
            section_dict = {
                "id": section.get("id"),
                "title": section.get("title", {}).get(language, section.get("title", {}).get("en")),
                "fields": []
            }

            for field in section.get("fields", []):
                field_dict = {
                    "id": field.get("id"),
                    "label": field.get("label", {}).get(language, field.get("label", {}).get("en")),
                    "type": field.get("type"),
                    "required": field.get("required", False),
                    "severity": field.get("severity", "optional")
                }

                # Add options if present
                if "options" in field:
                    field_dict["options"] = [
                        {
                            "value": opt.get("value"),
                            "label": opt.get("label", {}).get(language, opt.get("label", {}).get("en"))
                        }
                        for opt in field.get("options", [])
                    ]

                section_dict["fields"].append(field_dict)

            structure["sections"].append(section_dict)

        return structure

    def extract_field_data(self, document_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract form fields from document analysis
        Returns a dictionary of field_id -> value mappings
        """
        extracted_data = {}

        # Try to map analyzed fields to form fields
        analysis = document_analysis.get("analysis", {})

        # Direct mappings
        direct_mappings = {
            "project_title_en": "title",
            "primary_objective": "purpose",
            "field_of_study": "document_type"
        }

        for form_field, analysis_key in direct_mappings.items():
            if analysis_key in analysis:
                extracted_data[form_field] = analysis[analysis_key]

        return extracted_data

    def generate_empty_form_data(self) -> Dict[str, Any]:
        """Generate an empty form with all field IDs"""
        form_data = {}
        for field in self.get_all_fields():
            field_id = field.get("id")
            field_type = field.get("type")

            if field_type == "array":
                form_data[field_id] = []
            elif field_type in ["number"]:
                form_data[field_id] = None
            else:
                form_data[field_id] = ""

        return form_data


# Create a singleton instance
_form_schema = None

def get_form_schema() -> AP02FormSchema:
    """Get or create the form schema singleton"""
    global _form_schema
    if _form_schema is None:
        _form_schema = AP02FormSchema()
    return _form_schema
