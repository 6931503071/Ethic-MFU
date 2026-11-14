#!/bin/bash
# ไฟล์ test_api.sh - ทดสอบ API /api/analysis/fill ด้วย curl

# ⚙️ ตั้งค่า
API_URL="http://127.0.0.1:8050"
ENDPOINT="/api/analysis/fill"

# 📝 ข้อมูลทดสอบ (blocks ตัวอย่าง)
TEST_DATA='{
  "blocks": [
    {
      "index": 0,
      "text": "ชื่อโครงการวิจัย (Title)",
      "kind": "heading",
      "page": 1
    },
    {
      "index": 1,
      "text": "การศึกษาเปรียบเทียบประสิทธิผลของวิธีการรักษาโรคเบาหวาน",
      "kind": "text",
      "page": 1
    },
    {
      "index": 2,
      "text": "ชื่อภาษาอังกฤษ",
      "kind": "heading",
      "page": 1
    },
    {
      "index": 3,
      "text": "Comparative Effectiveness of Diabetes Treatment Methods",
      "kind": "text",
      "page": 1
    },
    {
      "index": 4,
      "text": "สาขาวิชาที่ทำการวิจัย",
      "kind": "heading",
      "page": 1
    },
    {
      "index": 5,
      "text": "แพทยศาสตร์ (สาขาโรคในระบบเผ่าเหล้า)",
      "kind": "text",
      "page": 1
    },
    {
      "index": 6,
      "text": "สถานที่ทำการวิจัย",
      "kind": "heading",
      "page": 2
    },
    {
      "index": 7,
      "text": "โรงพยาบาลรามาธิบดี ห้อง 301 ตึก A",
      "kind": "text",
      "page": 2
    }
  ],
  "template_id": "ap02_research_proposal"
}'

echo "🚀 ทดสอบ API: POST ${API_URL}${ENDPOINT}"
echo ""
echo "📤 ส่งข้อมูล:"
echo "$TEST_DATA" | jq .

echo ""
echo "⏳ กำลังรออยู่..."
echo ""

# 🔗 เรียก API
RESPONSE=$(curl -s -X POST \
  "${API_URL}${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -d "$TEST_DATA")

echo "📥 ได้ response:"
echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"

echo ""
echo "✅ ทดสอบเสร็จ"
