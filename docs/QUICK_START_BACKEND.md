# 🚀 QUICK START - AI Document Generator

## ⚡ 30 วินาที เตรียมการใช้งาน

### ขั้นตอนที่ 1: รัน Backend

**Windows:**
```bash
# Double-click ไฟล์นี้
C:\Users\User\Downloads\context\backend\START_BACKEND.bat
```

**macOS / Linux:**
```bash
cd C:\Users\User\Downloads\context\backend
bash START_BACKEND.sh
```

**ผลลัพธ์ที่ควรเห็น:**
```
╔════════════════════════════════════════════════╗
║  🚀 AI Document Generator API - Standalone    ║
╚════════════════════════════════════════════════╝

📍 Server URL:   http://127.0.0.1:8050
🏥 Health Check: http://127.0.0.1:8050/health
📤 Upload File:  POST http://127.0.0.1:8050/api/analysis/fill

⚡ Ready to accept requests...
```

### ขั้นตอนที่ 2: เปิด Frontend

1. เปิด File Explorer
2. ไปที่: `C:\Users\User\Downloads\context\`
3. Double-click `index.html`
4. Browser จะเปิดอัตโนมัติ

### ขั้นตอนที่ 3: ใช้งาน

1. **อัปโหลดเอกสาร** - ลากไฟล์ PDF/DOCX/TXT ลงในกล่อง
2. **เลือกตั้งค่า** - เลือก "Research Proposal" และภาษา
3. **คลิก "สร้างเอกสาร"** - รอประมาณ 2-3 วินาที
4. **ดูผลลัพธ์** - 4 รูปแบบเอกสารจะแสดงขึ้นมา
5. **ส่งออก** - คลิกดาวน์โหลด DOCX หรือ PDF

---

## ✅ เสร็จแล้ว!

```
Backend ✅ กำลังทำงาน
Frontend ✅ พร้อมใช้
API ✅ ตอบสนอง
```

---

## 🆘 ปัญหาเกิดขึ้น?

### ❌ Backend ไม่เริ่มต้น

**วิธีแก้:**
```bash
# ตรวจสอบ Python ติดตั้งแล้ว
python --version  # Should be 3.8+

# ลองรันด้วย Python อย่างชัดเจน
cd backend
python standalone_server.py
```

### ❌ "Address already in use" Error

Port 8050 ถูกใช้อยู่

**วิธีแก้:**
```bash
# ปิด process ที่ใช้ port
# Windows: Ctrl+C ที่ terminal แล้ว wait 5 วินาที
# macOS: lsof -i :8050 แล้ว kill <PID>
```

### ❌ Frontend ไม่ติดต่อ Backend

**วิธีแก้:**
1. ตรวจสอบ Backend ทำงานอยู่
2. เปิด Console ใน Browser (F12)
3. ดู error message สีแดง
4. ตรวจสอบ Frontend `js/api.js` บรรทัด 6 - URL ถูกต้องหรือไม่

---

## 📱 ทดสอบ API ด้วย Postman

1. เปิด Postman
2. สร้าง `POST` request ไป `http://localhost:8050/api/analysis/fill`
3. ไป Tab `Body` → `form-data`
4. เพิ่ม:
   - Key: `file` → เลือก file upload
   - Key: `category` → Value: `research_proposal`
   - Key: `language` → Value: `en`
5. คลิก "Send"

---

## 🎯 สิ่งที่ Backend ทำ

✅ รับไฟล์ PDF/DOCX/TXT  
✅ วิเคราะห์เนื้อหา  
✅ ตรวจหาข้อผิดพลาด  
✅ สร้าง 4 รูปแบบเอกสาร  
✅ ส่งคืน JSON response  

---

## 📊 Response Structure

```json
{
  "analysis": {
    "document_type": "Research Proposal",
    "language": "en",
    "purpose": "Research Ethics Submission",
    "errors": [],
    "missing_fields": ["[PLEASE ENTER RESEARCHER NAME]"]
  },
  "prototypes": [
    {
      "name": "Formal Academic Style",
      "content": "...",
      "highlighted_sections": ["Introduction"]
    },
    // ... 3 more prototypes
  ]
}
```

---

## 🛠️ Files ที่สำคัญ

```
C:\Users\User\Downloads\context\
├── backend/
│   ├── standalone_server.py          ← Backend ใหญ่
│   ├── START_BACKEND.bat             ← คลิกนี่ (Windows)
│   ├── START_BACKEND.sh              ← รันนี่ (Mac/Linux)
│   └── README.md                     ← More info
│
├── index.html                        ← Frontend หลัก
├── js/
│   ├── app.js                        ← Logic
│   └── api.js                        ← API client
└── css/
    └── style.css                     ← Styling
```

---

## 📞 Need Help?

1. **ดูเอกสาร:** `backend/README.md`
2. **ดู Logs:** ติดตามใน terminal ที่รัน backend
3. **ลอง Test API:** ใช้ Postman ตามด้านบน

---

**ทีนี้พร้อม! 🎉 ลองใช้งานเลย!**
