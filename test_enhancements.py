#!/usr/bin/env python3
"""
Comprehensive test of the AI Document Generator enhancements
"""

import sys
import os
sys.path.insert(0, '/c/Users/User/Downloads/Ethic-MFU')

print("=" * 60)
print("🧪 Testing AI Document Generator Enhancements")
print("=" * 60)

# Test 1: Check imports
print("\n1️⃣ Testing imports...")
try:
    from backend.app.utils.docx_exporter import create_docx
    from backend.app.utils.pdf_exporter import create_pdf
    from backend.app.utils.analyzer import analyze_document, create_field_metadata
    from backend.app.utils.prototype_generator import generate_prototypes
    print("✅ All imports successful")
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# Test 2: Test field metadata creation
print("\n2️⃣ Testing field metadata creation...")
try:
    test_text = """
    Research Title: Comparative Effectiveness Study
    Researcher: Dr. John Smith
    Institution: Mae Fah Luang University
    Date: 01/01/2026
    Field: Medicine
    """

    metadata = create_field_metadata(test_text, "research_proposal", {})
    required = [f for f in metadata if f['severity'] == 'required']
    ambiguous = [f for f in metadata if f['severity'] == 'ambiguous']

    print(f"✅ Generated {len(metadata)} fields total")
    print(f"   - Required (Red): {len(required)} fields")
    print(f"   - Ambiguous (Yellow/Orange): {len(ambiguous)} fields")

    if required:
        print(f"   - Example required field: {required[0]['label']}")
except Exception as e:
    print(f"❌ Field metadata error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Test document analysis
print("\n3️⃣ Testing document analysis...")
try:
    analysis = analyze_document(test_text, "research_proposal", "en")
    print(f"✅ Analysis complete")
    print(f"   - Document type: {analysis['document_type']}")
    print(f"   - Language: {analysis['language']}")
    print(f"   - Word count: {analysis['word_count']}")
    print(f"   - Fields with metadata: {len(analysis.get('field_metadata', []))}")
except Exception as e:
    print(f"❌ Analysis error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test prototype generation
print("\n4️⃣ Testing prototype generation...")
try:
    prototypes = generate_prototypes(test_text, "research_proposal", "en", analysis)
    print(f"✅ Generated {len(prototypes)} prototypes")
    for i, p in enumerate(prototypes):
        print(f"   - {i+1}. {p['name']}")
except Exception as e:
    print(f"❌ Prototype generation error: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Test DOCX export
print("\n5️⃣ Testing DOCX export...")
try:
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
    if os.path.exists(docx_path):
        size = os.path.getsize(docx_path)
        print(f"✅ DOCX created successfully")
        print(f"   - File: {docx_path}")
        print(f"   - Size: {size} bytes")
        os.remove(docx_path)  # Cleanup
    else:
        print(f"❌ DOCX file not found at {docx_path}")
except Exception as e:
    print(f"❌ DOCX export error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("✅ All tests completed!")
print("=" * 60)
