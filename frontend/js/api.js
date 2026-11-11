// จุดเรียก backend จุดเดียวของหน้าเว็บ
const API_BASE = "http://127.0.0.1:8050";

// แปลง error จาก backend ให้เป็นข้อความที่คนอ่านได้
function extractErrorMessage(data, status) {
  const d = data && data.detail;
  if (typeof d === "string") return d;
  if (d && typeof d === "object" && !Array.isArray(d) && d.message) return d.message;
  if (Array.isArray(d) && d.length) return "ข้อมูลที่ส่งไปไม่ถูกต้อง (รหัส " + status + ")";
  return "เกิดข้อผิดพลาด (รหัส " + status + ")";
}

// ส่งไฟล์ไปอ่าน+ตรวจ → POST /api/documents/analyze
// คืน { filename, file_type, page_count, blocks, suspects, summary }
async function analyzeDocument(file) {
  const formData = new FormData();
  formData.append("file", file);
  let response;
  try {
    response = await fetch(`${API_BASE}/api/documents/analyze`, {
      method: "POST",
      body: formData,
    });
  } catch (err) {
    throw new Error("เชื่อมต่อเซิร์ฟเวอร์ไม่ได้ ตรวจสอบว่า backend กำลังทำงานอยู่ (พอร์ต 8050)");
  }

  if (!response.ok) {
    let data = null;
    try { data = await response.json(); } catch (_) {}
    throw new Error(extractErrorMessage(data, response.status));
  }

  return response.json();
}

// ให้ AI ช่วยกรอกช่องจากข้อความที่อ่านแล้ว → POST /api/analysis/fill
// (ต้องผ่านการยืนยันของผู้ใช้ก่อนเรียกเสมอ)
async function fillFromAI(filename, blocks, mode) {
  const body = JSON.stringify({
    filename: filename || "",
    mode: mode || "draft",
    blocks: (blocks || []).map(b => ({
      index: b.index,
      text: b.text,
      kind: b.kind,
      page: b.page,
    })),
  });

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 300000); // ไฟล์ยาวอาจใช้ 1-3 นาที

  let response;
  try {
    response = await fetch(`${API_BASE}/api/analysis/fill`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      signal: ctrl.signal,
    });
  } catch (err) {
    if (err && err.name === "AbortError") {
      throw new Error("AI ตอบช้าเกินกำหนด กรุณาลองใหม่อีกครั้ง");
    }
    throw new Error("เชื่อมต่อเซิร์ฟเวอร์ไม่ได้ ตรวจสอบว่า backend กำลังทำงานอยู่ (พอร์ต 8050)");
  } finally {
    clearTimeout(timer);
  }

  if (!response.ok) {
    let data = null;
    try { data = await response.json(); } catch (_) {}
    throw new Error(extractErrorMessage(data, response.status));
  }

  return response.json();
}
