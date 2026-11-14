# 📖 คู่มือใช้ Postman ทดสอบ API ทีละขั้น

## 📥 ขั้นตอน 1: ดาวน์โหลด Postman

### Windows/Mac/Linux:
1. ไปที่ https://www.postman.com/downloads/
2. คลิก **"Download"** (เลือกระบบปฏิบัติการของคุณ)
3. รอดาวน์โหลด แล้ว install ตามปกติ
4. เปิด Postman

---

## ✅ ขั้นตอน 2: สร้าง Collection ใหม่ (สำหรับเก็บเรื่อง)

เมื่อเปิด Postman เป็นครั้งแรก จะเห็นหน้าต้อนรับ

### ทำนี้:
1. **ด้านซ้าย** ให้ดู "Collections" 
2. คลิกปุ่ม **"+" (สร้าง Collection ใหม่)**
3. ใส่ชื่อ: `Ethic-MFU`
4. คลิก **"Create"**

---

## 📨 ขั้นตอน 3: Import ไฟล์ Postman Collection

### วิธี A: Import ไฟล์ JSON (แนะนำ ⭐)

1. **ด้านบนสุด** ให้ดู Menu
2. คลิก **"File"** → **"Import"**
3. เลือก tab **"Upload Files"**
4. คลิก **"Select Files"**
5. ไปยัง `C:\Users\User\Downloads\context\`
6. เลือก **`ethic_mfu_postman.json`**
7. คลิก **"Open"**
8. คลิก **"Import"**

✅ ตอนนี้ Collection ของคุณจะมี Request พร้อมใช้แล้ว

---

## 🔧 ขั้นตอน 4: ตรวจสอบและแก้ไข Request

### หลังจาก Import ให้ทำนี้:

1. **ด้านซ้าย** ให้เห็น Collection `Ethic-MFU`
2. ขยาย (คลิกลูกศรหรือ + มาก ๆ) 
3. ต้องเห็น Request ชื่อ **"Test Fill Form API"**
4. **คลิกที่ชื่อ Request นั้น**

ตอนนี้หน้าจอควรมี 3 ส่วน:
- **ด้านบน:** Method + URL
- **ข้างบนกลาง:** Headers, Body, ...
- **ด้านล่าง:** Response (ยังว่าง)

---

## 📝 ขั้นตอน 5: ตรวจสอบ Method และ URL

**ด้านบนสุดสุด** ต้องเห็น:

```
POST   http://127.0.0.1:8050/api/analysis/fill
```

- **POST** = วิธีส่ง (ถูกต้อง ✅)
- **URL** = `http://127.0.0.1:8050/api/analysis/fill` (ถูกต้อง ✅)

ถ้าไม่ตรง ให้แก้ไข

---

## 🏷️ ขั้นตอน 6: ตรวจสอบ Headers

1. คลิก tab **"Headers"** (ใต้ URL)
2. ต้องเห็น:
   - `Key: Content-Type`
   - `Value: application/json`

✅ ถ้าเห็น แสดงว่าถูก

**ถ้าไม่เห็น ให้เพิ่ม:**
1. คลิก **"Add"** (ปุ่มเพิ่มแถวใหม่)
2. ใส่:
   - `Key: Content-Type`
   - `Value: application/json`

---

## 💾 ขั้นตอน 7: ตรวจสอบ Body (ข้อมูลที่ส่ง)

1. คลิก tab **"Body"** (ถัดจาก Headers)
2. ต้องเห็น **"raw"** ถูกเลือก (ลูกปุ่มสีเข้ม)
3. คลิก dropdown ถัดจาก "raw" → เลือก **"JSON"**
4. ด้านล่างจะเห็นข้อมูล JSON แบบนี้:

```json
{
  "blocks": [
    {
      "index": 0,
      "text": "ชื่อโครงการวิจัย (Title)",
      "kind": "heading",
      "page": 1
    },
    {
      "index": 1,
      "text": "การศึกษาเปรียบเทียบประสิทธิผลของการรักษา",
      "kind": "text",
      "page": 1
    },
    ...
  ],
  "template_id": "ap02_research_proposal"
}
```

✅ ถ้าเห็นแบบนี้ แสดงว่าพร้อมแล้ว

---

## 🚀 ขั้นตอน 8: ส่ง Request (ทดสอบ)

### ตรวจสอบก่อน:
- [ ] Backend กำลังรัน (ในสีดำ): `python -m uvicorn app.main:app --reload --port 8050`
- [ ] ไฟล์เทมเพลต `ap02_research_proposal.json` อยู่ที่ `backend/templates/`

### ส่ง Request:

**คลิกปุ่มสีน้ำเงิน "Send"** (ด้านขวาของ URL)

```
                          ← คลิกที่นี่
POST   http://127.0.0.1:8050/api/analysis/fill    [Send]
```

⏳ รอสัก 1-3 วินาที...

---

## 📥 ขั้นตอน 9: ดูผลลัพธ์ Response

### ด้านล่างจะแสดง Response:

#### ✅ ถ้า **สำเร็จ** (Status 200):

```
Status: 200 OK
```

และด้านล่างจะเห็น JSON:

```json
{
  "template_id": "ap02_research_proposal",
  "language": "th",
  "values": {
    "title_th": {
      "status": "found",
      "value": "การศึกษาเปรียบเทียบประสิทธิผลของการรักษา",
      "source_blocks": [1],
      "is_red": false
    },
    "title_en": {
      "status": "found",
      "value": "Comparative Effectiveness Study",
      "source_blocks": [2],
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
- `"status": "found"` = **ช่องสีเขียว** (ระบบหาเจอ)
- `"status": "missing"` = **ช่องสีแดง** (ระบบหาไม่เจอ)
- `"is_red": true` = ต้องแสดงเป็นสีแดง

---

#### ❌ ถ้า **ผิดพลาด** (Status 400, 500 เป็นต้น):

```
Status: 500 Internal Server Error
```

จะเห็นข้อความ error:

```json
{
  "detail": "เกิดข้อผิดพลาด: ..."
}
```

**บอกข้อความนี้ให้ฉันรู้** ฉันจะช่วยแก้ไข

---

## 🛠️ ขั้นตอน 10: ปรับแต่งและทดสอบใหม่ (ไม่บังคับ)

### ถ้าอยากเปลี่ยน blocks ทดสอบใหม่:

1. ใน tab **"Body"** ให้แก้ JSON
2. ลบบรรทัดที่ไม่ต้องการ หรือเพิ่มบรรทัดใหม่
3. คลิก **"Send"** ใหม่

**ตัวอย่าง: เพิ่ม block ชื่อผู้วิจัย**

```json
{
  "blocks": [
    {
      "index": 0,
      "text": "ชื่อโครงการวิจัย",
      "kind": "heading",
      "page": 1
    },
    {
      "index": 1,
      "text": "การศึกษาเปรียบเทียบ",
      "kind": "text",
      "page": 1
    },
    {
      "index": 2,
      "text": "ผู้วิจัยหลัก",
      "kind": "heading",
      "page": 2
    },
    {
      "index": 3,
      "text": "ศ.ดร. สมชาย ใจดี",
      "kind": "text",
      "page": 2
    }
  ],
  "template_id": "ap02_research_proposal"
}
```

คลิก **"Send"** → ดู response

---

## 📊 ตัวอย่างการอ่าน Response

### Response นี้หมายความว่า:

```json
{
  "values": {
    "title_th": {
      "status": "found",        ← ระบบหาเจอจากไฟล์
      "value": "การศึกษา...",  ← ค่าที่หาได้
      "source_blocks": [1],     ← มาจาก block หมายเลข 1
      "is_red": false           ← ไม่ต้องแสดงสีแดง
    },
    "pi_name": {
      "status": "missing",      ← ระบบหาไม่เจอ
      "value": null,            ← ไม่มีค่า
      "source_blocks": [],      ← ไม่พบ block
      "is_red": true            ← ต้องแสดงสีแดง (ผู้ใช้กรอกเอง)
    }
  }
}
```

---

## ✨ สรุป

### 🎯 ถ้าได้ Status 200 + มี "found" กับ "missing":

**ยินดีด้วย! API ทำงานได้แล้ว** 🎉

ขั้นตอนต่อไป:
1. ทดสอบกับ PDF จริง
2. ปรับ keywords ในโค้ด ถ้ายังจับไม่ได้
3. เพิ่ม keywords ให้ครบทั้ง 200+ field

---

## ❓ ติดตรงไหน?

### **ถ้า Status 500 Error:**
- ✅ ตรวจ Backend กำลังรันหรือไม่
- ✅ ตรวจ `ap02_research_proposal.json` อยู่ที่ `backend/templates/` หรือไม่

### **ถ้า Connection refused:**
- ✅ เปิด Backend: `python -m uvicorn app.main:app --reload --port 8050`
- ✅ รอให้ backend โหลดเสร็จ (เห็นข้อความ "Application startup complete")

### **ถ้า JSON error:**
- ✅ ตรวจ JSON syntax ที่ Body (ใช้ https://jsonlint.com/)
- ✅ ตรวจว่า key ถูกต้อง: `blocks`, `template_id`

---

**บอกมาว่าได้ผลไหม หรือติดตรงไหน ฉันมาช่วย** 😊

