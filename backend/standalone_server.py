"""
Standalone FastAPI Backend - No External Dependencies
Uses built-in Python libraries only
"""

import os
import json
import re
import base64
import zipfile
import io
from pathlib import Path
from typing import Dict, List, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading

# ============================================
# BUILT-IN HTTP SERVER (No FastAPI needed)
# ============================================

class DocumentHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for document processing"""

    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {
                "status": "healthy",
                "message": "API is running",
                "version": "1.0.0"
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        """Handle POST requests"""
        # CORS preflight
        if self.path == '/api/analysis/fill':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            try:
                # Parse multipart form data
                boundary = self.headers.get('Content-Type', '').split('boundary=')[1] if 'boundary=' in self.headers.get('Content-Type', '') else None

                if boundary:
                    data = self.parse_multipart(body, boundary)
                    response = self.analyze_document(data)

                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self.send_error(400, "Missing boundary in multipart data")

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                error_response = {"detail": f"Server error: {str(e)}"}
                self.wfile.write(json.dumps(error_response).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()

    def parse_multipart(self, body: bytes, boundary: str) -> Dict:
        """Parse multipart form data"""
        data = {}
        parts = body.split(f'--{boundary}'.encode())

        for part in parts:
            if b'Content-Disposition' in part:
                # Extract field name
                match = re.search(b'name="([^"]*)"', part)
                if match:
                    field_name = match.group(1).decode()

                    # Extract file name if present
                    filename_match = re.search(b'filename="([^"]*)"', part)

                    # Extract content
                    content_start = part.find(b'\r\n\r\n')
                    if content_start != -1:
                        content = part[content_start + 4:]
                        # Remove trailing boundary
                        content = content.rstrip(b'\r\n')

                        if filename_match:
                            filename = filename_match.group(1).decode()
                            data[field_name] = {
                                'filename': filename,
                                'content': content
                            }
                        else:
                            data[field_name] = content.decode()

        return data

    def analyze_document(self, data: Dict) -> Dict:
        """Analyze document and return prototypes"""

        # Extract file and metadata
        file_data = data.get('file', {})
        if isinstance(file_data, dict):
            file_content = file_data.get('content', b'')
            filename = file_data.get('filename', 'document')
        else:
            file_content = file_data.encode() if isinstance(file_data, str) else file_data
            filename = 'document'

        category = data.get('category', 'general')
        language = data.get('language', 'en')
        notes = data.get('notes', '')

        # Extract text from document
        try:
            text = self.extract_text(file_content, filename)
        except Exception as e:
            return {
                "detail": f"Error parsing document: {str(e)}"
            }

        if not text or len(text.strip()) < 10:
            return {
                "detail": "Document appears to be empty or unreadable"
            }

        # Analyze
        analysis = self.analyze_text(text, category, language)

        # Generate prototypes
        prototypes = self.generate_prototypes(text, category, language, analysis)

        return {
            "analysis": analysis,
            "prototypes": prototypes,
            "metadata": {
                "file_name": filename,
                "file_size": len(file_content),
                "category": category,
                "language": language
            }
        }

    def extract_text(self, file_content: bytes, filename: str) -> str:
        """Extract text from document"""
        ext = Path(filename).suffix.lower()

        if ext == '.txt':
            return file_content.decode('utf-8', errors='ignore')

        elif ext == '.pdf':
            # Simple PDF text extraction (no external library)
            text = file_content.decode('latin-1', errors='ignore')
            # Remove PDF binary data, keep readable text
            text = re.sub(r'[^\x20-\x7E\n\r\t฀-๿]', '', text)
            return text

        elif ext == '.docx':
            # DOCX is a ZIP file - extract XML
            try:
                with zipfile.ZipFile(io.BytesIO(file_content)) as docx:
                    xml_content = docx.read('word/document.xml').decode('utf-8')
                    # Remove XML tags
                    text = re.sub(r'<[^>]+>', '', xml_content)
                    return text
            except:
                return ""

        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def analyze_text(self, text: str, category: str, language: str) -> Dict:
        """Analyze document text"""

        # Detect Thai/English
        thai_chars = sum(1 for c in text if '฀' <= c <= '๿')
        english_chars = sum(1 for c in text if c.isalpha() and ord(c) < 128)
        detected_lang = 'th' if thai_chars > english_chars else 'en'

        # Find errors
        errors = []
        if '[TODO]' in text or '[PLACEHOLDER]' in text:
            errors.append("Document contains placeholder markers")
        if '  ' in text:
            errors.append("Multiple spaces detected")

        # Find missing fields
        missing = self.detect_missing_fields(text, category)

        return {
            "document_type": self.map_category(category),
            "language": detected_lang,
            "purpose": self.get_purpose(category),
            "status": "Complete",
            "word_count": len(text.split()),
            "page_estimate": len(text.split()) // 250,
            "errors": errors,
            "missing_fields": missing
        }

    def generate_prototypes(self, text: str, category: str, language: str, analysis: Dict) -> List[Dict]:
        """Generate 4 document prototypes"""

        base_name = "Prototype"
        if language == 'th':
            names = ["รูปแบบการเขียนวิชาการ", "รูปแบบธุรกิจ", "รูปแบบการบรรยาย", "รูปแบบโครงสร้างมาตรฐาน"]
            descriptions = [
                "สไตล์การเขียนอย่างเป็นทางการ",
                "สไตล์การเขียนกระชับและชัดเจน",
                "สไตล์การบรรยายรายละเอียด",
                "สไตล์ที่มีโครงสร้างชัดเจน"
            ]
        else:
            names = ["Formal Academic Style", "Concise Business Style", "Narrative Detailed Style", "Structured Template Style"]
            descriptions = [
                "Comprehensive academic approach",
                "Direct and focused presentation",
                "Story-like presentation",
                "Organized format with clear sections"
            ]

        prototypes = []
        styles = ["academic", "business", "narrative", "structured"]

        for i in range(4):
            # Create variation of text
            if i == 1:
                # Concise version - shorter
                content = text[:len(text)//2] if len(text) > 200 else text
            elif i == 2:
                # Expand with transitions
                content = f"In detail, {text}"
            elif i == 3:
                # Add structure
                lines = text.split('\n')
                content = "\n".join([f"• {line}" for line in lines if line.strip()][:10])
            else:
                content = text

            prototype = {
                "name": names[i],
                "description": descriptions[i],
                "style": styles[i],
                "content": content[:500],  # Limit length for demo
                "highlighted_sections": self.extract_sections(text),
                "notes": f"Prototype {i+1} - {descriptions[i]}"
            }
            prototypes.append(prototype)

        return prototypes

    def map_category(self, category: str) -> str:
        """Map category to type"""
        mapping = {
            "research_proposal": "Research Proposal (AP 02/2026)",
            "ethics_submission": "Ethics Submission Document",
            "general": "General Document",
            "administrative": "Administrative Document"
        }
        return mapping.get(category, "Document")

    def get_purpose(self, category: str) -> str:
        """Get document purpose"""
        purposes = {
            "research_proposal": "Research Ethics Committee Submission",
            "ethics_submission": "Research Ethics Submission",
            "general": "General Administrative Use",
            "administrative": "Administrative Processing"
        }
        return purposes.get(category, "Unknown")

    def detect_missing_fields(self, text: str, category: str) -> List[str]:
        """Detect missing required fields"""
        missing = []

        if not re.search(r'(Dr\.|Prof\.|Researcher|PI)', text, re.IGNORECASE):
            missing.append("[PLEASE ENTER RESEARCHER NAME]")
            missing.append("[PLEASE ENTER RESEARCHER AFFILIATION]")

        if not re.search(r'(title|objective)', text, re.IGNORECASE):
            missing.append("[PLEASE ENTER RESEARCH TITLE]")

        if category == "research_proposal":
            missing.append("[PLEASE ENTER ETHICS APPROVAL NUMBER]")
            missing.append("[PLEASE ENTER PROJECT DATES]")

        return missing[:5]

    def extract_sections(self, text: str) -> List[str]:
        """Extract key sections"""
        sections = []
        keywords = [
            'introduction', 'background', 'objective', 'method',
            'result', 'discussion', 'conclusion', 'reference'
        ]

        for keyword in keywords:
            if re.search(keyword, text, re.IGNORECASE):
                sections.append(keyword.capitalize())

        return sections[:5]

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


# ============================================
# MAIN SERVER
# ============================================

def run_server(host='127.0.0.1', port=8050):
    """Run the HTTP server"""
    server_address = (host, port)
    httpd = HTTPServer(server_address, DocumentHandler)

    print(f"""
╔════════════════════════════════════════════════╗
║  🚀 AI Document Generator API - Standalone    ║
╚════════════════════════════════════════════════╝

📍 Server URL:   http://{host}:{port}
🏥 Health Check: http://{host}:{port}/health
📤 Upload File:  POST http://{host}:{port}/api/analysis/fill

⚡ Ready to accept requests...
Press CTRL+C to stop
""")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ Server stopped")
        httpd.shutdown()


if __name__ == '__main__':
    run_server()
