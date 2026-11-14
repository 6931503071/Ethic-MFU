#!/usr/bin/env python3
"""
Quick test script for DOCX exporter
Run this to verify the exporter works
"""

import sys
sys.path.insert(0, '/c/Users/User/Downloads/Ethic-MFU')

from backend.app.utils.docx_exporter import create_docx

# Create sample test data
test_data = {
    "analysis": {
        "document_type": "Research Proposal (AP 02/2026)",
        "language": "th",
        "purpose": "Research Ethics Committee Submission",
        "status": "Complete",
        "word_count": 250,
        "page_estimate": 1,
        "errors": ["Found 3 unfilled placeholders"],
        "warnings": ["Document is relatively short"],
        "field_metadata": [
            {
                "id": "title_th",
                "label": "Research Title (Thai)",
                "page": 1,
                "severity": "required",
                "confidence": 0,
                "status": "empty"
            },
            {
                "id": "field_of_study",
                "label": "Field of Study",
                "page": 1,
                "severity": "ambiguous",
                "confidence": 75,
                "status": "filled"
            }
        ]
    },
    "prototypes": [
        {
            "name": "รูปแบบการเขียนวิชาการ",
            "description": "สไตล์การเขียนอย่างเป็นทางการ",
            "content": "[PLEASE ENTER RESEARCH TITLE]\nการศึกษาเปรียบเทียบประสิทธิผล\n[PLEASE ENTER RESEARCHER NAME]",
            "highlighted_sections": ["Introduction", "Methodology"]
        }
    ],
    "metadata": {
        "file_name": "test_document.pdf",
        "file_size": 1024,
        "category": "research_proposal",
        "language": "th"
    }
}

try:
    result = create_docx(test_data)
    print(f"✅ DOCX created successfully: {result}")

    # Check if file exists
    import os
    if os.path.exists(result):
        size = os.path.getsize(result)
        print(f"✅ File size: {size} bytes")
    else:
        print("❌ File was not created")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
