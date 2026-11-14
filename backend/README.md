# 🚀 Backend API - AI Document Generator

Backend API ที่สร้างจาก FastAPI สำหรับวิเคราะห์และสร้างเอกสาร

## 📋 ข้อกำหนด

- Python 3.8+
- pip (Python package manager)

## ⚙️ ติดตั้ง

### ขั้นตอนที่ 1: ติดตั้ง Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**ผลลัพธ์ที่คาดหวัง:**
```
Successfully installed fastapi uvicorn python-multipart python-docx PyPDF2 ...
```

### ขั้นตอนที่ 2: รัน Backend

```bash
python -m uvicorn app.main:app --reload --port 8050
```

**ผลลัพธ์ที่คาดหวัง:**
```
INFO:     Uvicorn running on http://127.0.0.1:8050 (Press CTRL+C to quit)
```

## 🔌 API Endpoints

### 1. Health Check
- **URL:** `GET /health`
- **ตอบสนอง:** `{"status": "healthy", "message": "API is running"}`

### 2. Analyze and Fill Document
- **URL:** `POST /api/analysis/fill`
- **Parameters:**
  - `file` (File): PDF, DOCX, หรือ TXT
  - `category` (String): research_proposal, ethics_submission, general, administrative
  - `language` (String): en, th, both
  - `notes` (String): ข้อมูลเพิ่มเติม (optional)

**ตัวอย่าง Response:**
```json
{
  "analysis": {
    "document_type": "Research Proposal",
    "language": "en",
    "purpose": "Research Ethics Committee Submission",
    "status": "Complete",
    "errors": [],
    "missing_fields": ["[PLEASE ENTER RESEARCHER NAME]"]
  },
  "prototypes": [
    {
      "name": "Formal Academic Style",
      "description": "Academic formal version",
      "content": "...",
      "highlighted_sections": ["Introduction"]
    },
    // ... 3 more prototypes
  ]
}
```

### 3. Export to DOCX
- **URL:** `POST /api/export/docx`
- **Parameters:** JSON data (from prototypes)
- **Returns:** DOCX file

### 4. Export to PDF
- **URL:** `POST /api/export/pdf`
- **Parameters:** JSON data (from prototypes)
- **Returns:** PDF file

## 📂 โครงสร้างไฟล์

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    ← Main FastAPI app
│   └── utils/
│       ├── __init__.py
│       ├── document_parser.py     ← Parse PDF/DOCX/TXT
│       ├── analyzer.py             ← Analyze documents
│       └── prototype_generator.py  ← Generate 4 prototypes
├── requirements.txt               ← Dependencies
└── README.md                       ← นี่แหละ
```

## 🧪 ทดสอบ API

### วิธีที่ 1: ใช้ Postman
1. Import collection จาก `C:\Users\User\Downloads\context\ethic_mfu_postman.json`
2. ส่ง request ไป `POST http://localhost:8050/api/analysis/fill`
3. เลือกไฟล์ PDF/DOCX/TXT ที่อัปโหลด

### วิธีที่ 2: ใช้ curl

```bash
curl -X POST http://localhost:8050/api/analysis/fill \
  -F "file=@your_document.pdf" \
  -F "category=research_proposal" \
  -F "language=en"
```

### วิธีที่ 3: ใช้ Frontend
1. เปิด `C:\Users\User\Downloads\context\index.html`
2. อัปโหลดเอกสาร
3. เลือกตั้งค่า
4. คลิก "สร้างเอกสาร"

## 🐛 Debug & Troubleshooting

### ❌ Error: "ModuleNotFoundError: No module named 'fastapi'"

**วิธีแก้:**
```bash
pip install -r requirements.txt
```

### ❌ Error: "Address already in use"

Port 8050 ถูกใช้อยู่แล้ว ให้เปลี่ยน port:
```bash
python -m uvicorn app.main:app --reload --port 8051
```

แล้วแก้ไข Frontend `js/api.js` บรรทัด 6:
```javascript
const API_BASE_URL = 'http://localhost:8051';
```

### ❌ Error: "CORS Error"

CORS ถูกเปิด automatic ใน `app/main.py` ของ backend

### ❌ PDF Parse Error

ตรวจสอบ PyPDF2 ติดตั้งแล้ว:
```bash
pip install PyPDF2 --upgrade
```

## 📊 API Response Structure

### Successful Response (200 OK)
```json
{
  "analysis": {
    "document_type": "string",
    "language": "string",
    "purpose": "string",
    "status": "string",
    "word_count": 1234,
    "page_estimate": 5,
    "errors": [],
    "warnings": [],
    "missing_fields": []
  },
  "prototypes": [
    {
      "name": "string",
      "description": "string",
      "style": "string",
      "content": "string",
      "highlighted_sections": [],
      "notes": "string"
    }
  ],
  "metadata": {
    "file_name": "string",
    "file_size": 1234,
    "category": "string",
    "language": "string"
  }
}
```

### Error Response
```json
{
  "detail": "Error message here"
}
```

## 🚀 Production Deployment

สำหรับ production ให้เปลี่ยน:

**ไฟล์: `app/main.py` บรรทัด 40**
```python
# ❌ Development (อันตราย)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Allow all - NOT SAFE
)

# ✅ Production (ปลอดภัย)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific origin
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

## 📞 Support

หากมีปัญหา ตรวจสอบ:

1. **Backend ทำงานหรือไม่:**
   ```bash
   curl http://localhost:8050/health
   ```

2. **ติดตั้ง dependencies ครบหรือไม่:**
   ```bash
   pip list | grep fastapi
   ```

3. **Python version ถูกต้องหรือไม่:**
   ```bash
   python --version  # Should be 3.8+
   ```

4. **ดู Error Logs:**
   ดูใน terminal ที่รัน backend

## 📝 Notes

- API ช่วยเวลา 30 วินาที (timeout)
- ไฟล์ maximum 10MB
- Supports: PDF, DOCX, TXT
- Output: JSON + 4 prototypes

---

✅ Backend พร้อม! ทีนี้สามารถใช้ Frontend ได้เลย 🎉
