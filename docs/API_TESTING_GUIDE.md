# 🧪 คู่มือทดสอบ API /api/analysis/fill

## 📋 ตรวจสอบก่อนทดสอบ

### 1. ✅ ตรวจสอบไฟล์เทมเพลต

**ต้อง:** `backend/templates/ap02_research_proposal.json` มีอยู่

```bash
# Windows (Command Prompt)
dir backend\templates\ap02_research_proposal.json

# Linux/Mac
ls -la backend/templates/ap02_research_proposal.json
```

ถ้าไม่เห็น ให้คัดลอกไฟล์ `ap02_research_proposal.json` ที่ให้มาไปที่ `backend/templates/`

---

### 2. ✅ เช็ก Backend กำลังรันอยู่หรือไม่

```bash
# ที่ terminal ที่รัน backend ต้องเห็นข้อความแบบนี้:
# INFO:     Uvicorn running on http://127.0.0.1:8050
# INFO:     Application startup complete
```

ถ้าไม่รัน:
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8050
```

---

## 🧪 วิธีทดสอบ API (3 วิธี)

### **วิธี 1️⃣: ใช้ curl ในสิ่งสั่ง (Command Line)**

#### **Windows (PowerShell)**

```powershell
# ก็อปโค้ดนี้ไปวาง Terminal
$body = @{
    blocks = @(
        @{ index=0; text="ชื่อโครงการวิจัย"; kind="heading"; page=1 },
        @{ index=1; text="การศึกษาเปรียบเทียบประสิทธิผล"; kind="text"; page=1 },
        @{ index=2; text="สาขาวิชา"; kind="heading"; page=1 },
        @{ index=3; text="แพทยศาสตร์"; kind="text"; page=1 }
    )
    template_id = "ap02_research_proposal"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://127.0.0.1:8050/api/analysis/fill" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body $body | ConvertTo-Json | Write-Host
```

#### **Linux/Mac (Bash)**

```bash
curl -X POST http://127.0.0.1:8050/api/analysis/fill \
  -H "Content-Type: application/json" \
  -d '{
    "blocks": [
      {"index": 0, "text": "ชื่อโครงการวิจัย", "kind": "heading", "page": 1},
      {"index": 1, "text": "การศึกษาเปรียบเทียบประสิทธิผล", "kind": "text", "page": 1},
      {"index": 2, "text": "สาขาวิชา", "kind": "heading", "page": 1},
      {"index": 3, "text": "แพทยศาสตร์", "kind": "text", "page": 1}
    ],
    "template_id": "ap02_research_proposal"
  }' | python -m json.tool
```

---

### **วิธี 2️⃣: ใช้ Postman (GUI)**

#### **ขั้นตอน:**

1. **ดาวน์โหลด Postman** (ถ้ายังไม่มี)
   - https://www.postman.com/downloads/

2. **เปิด Postman และสร้าง Request ใหม่**
   - คลิก "New" → "Request"
   - ใส่ชื่อ เช่น "Test Fill Form"

3. **ตั้งค่า Request:**
   - **Method:** POST
   - **URL:** `http://127.0.0.1:8050/api/analysis/fill`
   
4. **ตั้ง Header:**
   - คลิก "Headers" tab
   - เพิ่ม: `Key: Content-Type` → `Value: application/json`

5. **ใส่ Body:**
   - คลิก "Body" tab
   - เลือก "raw" → "JSON"
   - วาง JSON นี้:

```json
{
  "blocks": [
    {"index": 0, "text": "ชื่อโครงการวิจัย (Title)", "kind": "heading", "page": 1},
    {"index": 1, "text": "การศึกษาเปรียบเทียบประสิทธิผลของวิธีการรักษา", "kind": "text", "page": 1},
    {"index": 2, "text": "ชื่อภาษาอังกฤษ", "kind": "heading", "page": 1},
    {"index": 3, "text": "Comparative Study of Treatment Methods", "kind": "text", "page": 1},
    {"index": 4, "text": "สาขาวิชาที่ทำการวิจัย", "kind": "heading", "page": 2},
    {"index": 5, "text": "แพทยศาสตร์ (สาขาโรคในระบบ)", "kind": "text", "page": 2}
  ],
  "template_id": "ap02_research_proposal"
}
```

6. **คลิก "Send"**
   - รอรับ response

---

### **วิธี 3️⃣: ใช้ไฟล์ test_api.sh (Linux/Mac)**

```bash
# 1. เปิด Terminal
# 2. ไปยังโฟลเดอร์ที่เก็บไฟล์
cd /path/to/test_api.sh

# 3. รันไฟล์
chmod +x test_api.sh
./test_api.sh
```

---

## ✅ ผลลัพธ์ที่คาดหวัง

### **Success Response (HTTP 200)**

```json
{
  "template_id": "ap02_research_proposal",
  "language": "th",
  "values": {
    "title_th": {
      "status": "found",
      "value": "การศึกษาเปรียบเทียบประสิทธิผลของวิธีการรักษา",
      "source_blocks": [1],
      "is_red": false
    },
    "title_en": {
      "status": "found",
      "value": "Comparative Study of Treatment Methods",
      "source_blocks": [3],
      "is_red": false
    },
    "field_of_study": {
      "status": "found",
      "value": "แพทยศาสตร์ (สาขาโรคในระบบ)",
      "source_blocks": [5],
      "is_red": false
    },
    "pi_name": {
      "status": "missing",
      "value": null,
      "source_blocks": [],
      "is_red": true
    }
  }
}
```

**อธิบาย:**
- `status: "found"` = ระบบหาเจอจากไฟล์ (สีเขียว)
- `status: "missing"` = ระบบหาไม่เจอ (สีแดง)
- `is_red: true` = ต้องแสดงสีแดง
- `source_blocks: [...]` = หมายเลข block ที่พบ

---

## ❌ หากเกิด Error

### **Error 1: "Connection refused"**

```
curl: (7) Failed to connect to 127.0.0.1 port 8050
```

**แก้:** Backend ไม่ได้รัน ต้องเปิด terminal ใหม่แล้วรัน:
```bash
python -m uvicorn app.main:app --reload --port 8050
```

---

### **Error 2: "Template not found"**

```json
{
  "detail": "โหลดเทมเพลต ap02_research_proposal ล้มเหลว: ..."
}
```

**แก้:** ไฟล์ `ap02_research_proposal.json` ไม่อยู่ที่ `backend/templates/`

ตรวจสอบ:
```bash
ls -la backend/templates/
```

---

### **Error 3: "Invalid blocks format"**

```json
{
  "detail": "ต้องส่ง blocks"
}
```

**แก้:** JSON ที่ส่งไม่มี `blocks` หรือ `blocks` เป็นรูปแบบผิด

ตรวจสอบ JSON:
- `blocks` ต้องเป็น array
- แต่ละ block ต้องมี: `index`, `text`, `kind`, `page`

---

### **Error 4: "Template validation error"**

```json
{
  "detail": "เทมเพลตมีปัญหา: ..."
}
```

**แก้:** JSON template มีข้อมูลไม่ถูกต้อง

ตรวจสอบ `ap02_research_proposal.json`:
- ตรวจ JSON syntax (ใช้ https://jsonlint.com/)
- ตรวจว่า `id` ตรงกับ `template_id` ที่ส่ง

---

## 📝 ทดสอบทีละขั้น

### **ขั้น 1: ทดสอบ blocks ง่าย ๆ**

```json
{
  "blocks": [
    {"index": 0, "text": "ชื่อโครงการวิจัย", "kind": "text", "page": 1},
    {"index": 1, "text": "การศึกษาแรก", "kind": "text", "page": 1}
  ],
  "template_id": "ap02_research_proposal"
}
```

ถ้าได้ response ก็ไป ขั้น 2

---

### **ขั้น 2: เพิ่ม blocks มากขึ้น**

```json
{
  "blocks": [
    {"index": 0, "text": "ชื่อโครงการวิจัย", "kind": "heading", "page": 1},
    {"index": 1, "text": "การศึกษาเปรียบเทียบ", "kind": "text", "page": 1},
    {"index": 2, "text": "ชื่อภาษาอังกฤษ", "kind": "heading", "page": 1},
    {"index": 3, "text": "Comparative Study", "kind": "text", "page": 1},
    {"index": 4, "text": "สาขาวิชา", "kind": "heading", "page": 2},
    {"index": 5, "text": "แพทยศาสตร์", "kind": "text", "page": 2}
  ],
  "template_id": "ap02_research_proposal"
}
```

---

### **ขั้น 3: ทดสอบกับ PDF จริง**

เมื่อทั้ง 2 ขั้นผ่าน ให้:
1. อัปโหลด PDF จริง
2. คัดลอก blocks จาก console เก็บเป็น JSON
3. ส่งไป API อีกครั้ง

---

## 🎯 ความสำเร็จ

✅ เมื่อได้ response ที่มี:
- `template_id` ถูกต้อง
- บางช่องมี `status: "found"` (สีเขียว)
- บางช่องมี `status: "missing"` (สีแดง)

แสดงว่า API ทำงานได้ ✨

