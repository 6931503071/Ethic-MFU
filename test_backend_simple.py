#!/usr/bin/env python3
"""
Quick debug script to test the backend
"""

import sys
sys.path.insert(0, '/c/Users/User/Downloads/Ethic-MFU')

from backend.app.utils.document_parser import parse_document
from backend.app.utils.analyzer import analyze_document
from backend.app.utils.prototype_generator import generate_prototypes

# Create sample test data
sample_text = """
Research Title: Comparative Effectiveness Study
Researcher: Dr. John Smith
Institution: Mae Fah Luang University
Date: 01/01/2026
Field: Medicine

This is a research proposal about diabetes treatment. The study aims to compare different treatment methods.
"""

print("=" * 60)
print("🧪 Backend Test")
print("=" * 60)

try:
    print("\n1️⃣ Testing analyze_document...")
    analysis = analyze_document(sample_text, "research_proposal", "en")
    print(f"✅ Analysis complete")
    print(f"   - Document type: {analysis['document_type']}")
    print(f"   - Missing fields: {len(analysis['missing_fields'])}")
    print(f"   - Field metadata: {len(analysis.get('field_metadata', []))}")

    print("\n2️⃣ Testing generate_prototypes...")
    prototypes = generate_prototypes(sample_text, "research_proposal", "en", analysis)
    print(f"✅ Generated {len(prototypes)} prototypes")
    for i, p in enumerate(prototypes):
        print(f"   - {i+1}. {p['name']}")

    print("\n3️⃣ Testing DOCX export...")
    from backend.app.utils.docx_exporter import create_docx

    test_data = {
        "analysis": analysis,
        "prototypes": prototypes,
        "metadata": {
            "file_name": "test.txt",
            "file_size": 1024,
            "category": "research_proposal",
            "language": "en"
        }
    }

    docx_path = create_docx(test_data)
    import os
    if os.path.exists(docx_path):
        size = os.path.getsize(docx_path)
        print(f"✅ DOCX created")
        print(f"   - File: {docx_path}")
        print(f"   - Size: {size} bytes")
        os.remove(docx_path)
    else:
        print(f"❌ DOCX file not found")

    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
