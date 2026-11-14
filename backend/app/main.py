"""
FastAPI Backend for AI Document Generator
Handles document analysis and prototype generation
"""

import os
import json
import tempfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import uvicorn

# Import document processing modules
from app.utils.document_parser import parse_document
from app.utils.analyzer import analyze_document, detect_missing_fields
from app.utils.prototype_generator import generate_prototypes

# Import form-related modules
from app.routes.form_routes import router as form_router
from app.routes.document_routes import router as document_router

# ============================================
# APP INITIALIZATION
# ============================================

app = FastAPI(
    title="AI Document Generator API",
    description="API for analyzing and generating research documents",
    version="1.0.0"
)

# ============================================
# CORS CONFIGURATION
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# INCLUDE ROUTERS
# ============================================

app.include_router(form_router)
app.include_router(document_router)

# ============================================
# ROUTES
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "API is running",
        "version": "1.0.0"
    }


@app.post("/api/analysis/fill")
async def analyze_and_fill(
    file: UploadFile = File(...),
    category: str = Form(...),
    language: str = Form(default="en"),
    notes: str = Form(default="")
):
    """
    Main endpoint: Analyze document and generate prototypes

    Parameters:
    - file: Uploaded document (PDF, DOCX, or TXT)
    - category: Document category (research_proposal, ethics_submission, etc.)
    - language: Output language (en, th, both)
    - notes: Additional user notes

    Returns:
    - analysis: Document analysis results
    - prototypes: 4 document prototypes with different styles
    """

    try:
        # ============================================
        # VALIDATE FILE
        # ============================================

        allowed_extensions = {'.pdf', '.docx', '.txt'}
        file_ext = Path(file.filename).suffix.lower()

        if file_ext not in allowed_extensions:
            return JSONResponse(
                status_code=400,
                content={"detail": f"File type {file_ext} not supported"}
            )

        # ============================================
        # READ FILE CONTENT
        # ============================================

        file_content = await file.read()

        # Parse document based on file type
        try:
            extracted_text = parse_document(file_content, file_ext)
        except Exception as e:
            return JSONResponse(
                status_code=400,
                content={"detail": f"Error parsing document: {str(e)}"}
            )

        if not extracted_text or len(extracted_text.strip()) < 10:
            return JSONResponse(
                status_code=400,
                content={"detail": "Document appears to be empty or unreadable"}
            )

        # ============================================
        # ANALYZE DOCUMENT
        # ============================================

        analysis = analyze_document(
            text=extracted_text,
            document_type=category,
            language=language
        )

        # Detect missing fields
        missing_fields = detect_missing_fields(extracted_text, category)
        analysis["missing_fields"] = missing_fields

        # ============================================
        # GENERATE 4 PROTOTYPES
        # ============================================

        prototypes = generate_prototypes(
            original_text=extracted_text,
            category=category,
            language=language,
            analysis=analysis,
            user_notes=notes
        )

        # ============================================
        # BUILD RESPONSE
        # ============================================

        response = {
            "analysis": analysis,
            "prototypes": prototypes,
            "metadata": {
                "file_name": file.filename,
                "file_size": len(file_content),
                "category": category,
                "language": language
            }
        }

        return response

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Server error: {str(e)}"}
        )


@app.post("/api/export/docx")
async def export_to_docx(data: dict):
    """
    Export generated document to DOCX format

    Parameters:
    - data: Document content and metadata

    Returns:
    - DOCX file for download
    """

    try:
        from app.utils.docx_exporter import create_docx

        # Create DOCX file
        docx_file = create_docx(data)

        return FileResponse(
            path=docx_file,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="generated_document.docx"
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Export error: {str(e)}"}
        )


@app.post("/api/export/pdf")
async def export_to_pdf(data: dict):
    """
    Export generated document to PDF format

    Parameters:
    - data: Document content and metadata

    Returns:
    - PDF file for download
    """

    try:
        from app.utils.pdf_exporter import create_pdf

        # Create PDF file
        pdf_file = create_pdf(data)

        return FileResponse(
            path=pdf_file,
            media_type="application/pdf",
            filename="generated_document.pdf"
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Export error: {str(e)}"}
        )


# ============================================
# STARTUP
# ============================================

if __name__ == "__main__":
    print("🚀 Starting AI Document Generator API...")
    print("📍 http://localhost:8050")
    print("📚 API Docs: http://localhost:8050/docs")

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8050,
        reload=True
    )
