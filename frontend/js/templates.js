/**
 * templates.js — fixed templates, chosen via the "หมวดหมู่เอกสาร" dropdown
 * ------------------------------------------------------------------------
 * Each template `id` MUST equal the <option value> in #docCategory (index.html).
 * Flow: choose category -> "สร้างเอกสาร" -> preview in page -> download original .docx
 * Real Word files must exist in frontend/templates/.
 * Page must be served over http:// (Live Server is fine), not file://.
 */
const DOCUMENT_TEMPLATES = [
    {
        id: 'ap02_th',
        title: 'AP 02/2026 แบบเสนอโครงการวิจัยเพื่อพิจารณา (ภาษาไทย)',
        file: 'templates/ap02_th.docx',
        downloadName: 'AP 02_2026 แบบเสนอโครงการวิจัยเพื่อพิจารณา.docx',
    },
    {
        id: 'ap02_en',
        title: 'AP 02/2026 Research Protocol Proposal Form (English)',
        file: 'templates/ap02_en.docx',
        downloadName: 'AP 02_2026 Research Protocol Proposal Form.docx',
    },
    {
        id: 'memo_th',
        title: 'บันทึกข้อความ',
        file: 'templates/memo_th.docx',
        downloadName: 'บันทึกข้อความ.docx',
    },
    {
        id: 'letter_th',
        title: 'หนังสือภายนอก',
        file: 'templates/letter_th.docx',
        downloadName: 'หนังสือภายนอก.docx',
    },
];

let currentTemplate = null;       // template shown in preview
let currentTemplateBuffer = null; // original bytes (never modified)

/** Template that belongs to the selected category, or null (= use AI flow). */
function getSelectedTemplate() {
    const sel = document.getElementById('docCategory');
    const v = sel ? sel.value : '';
    return DOCUMENT_TEMPLATES.find(t => t.id === v) || null;
}

/** Fetch template bytes; verify it is a real .docx (ZIP signature "PK"). */
async function loadTemplateBuffer(tpl) {
    let res;
    try { res = await fetch(tpl.file, { cache: 'no-cache' }); }
    catch (e) {
        throw new Error('โหลดแม่แบบไม่ได้ — ต้องเปิดหน้าเว็บผ่าน http:// (ไม่ใช่ file://)');
    }
    if (!res.ok) throw new Error(`ไม่พบไฟล์แม่แบบ "${tpl.file}" (HTTP ${res.status}) — ตรวจสอบโฟลเดอร์ frontend/templates`);
    const buf = await res.arrayBuffer();
    const sig = new Uint8Array(buf.slice(0, 2));
    if (sig[0] !== 0x50 || sig[1] !== 0x4B) {
        throw new Error(`ไฟล์ "${tpl.file}" ไม่ใช่ไฟล์ .docx จริง — โปรดใช้ไฟล์ Word ต้นฉบับ`);
    }
    return buf;
}

/** Render the template inside #templatePreview. Throws Error with a Thai message. */
async function previewTemplate(tpl) {
    if (!window.docx || !window.JSZip) {
        throw new Error('ไม่พบไลบรารีพรีวิว — ตรวจสอบว่ามี lib/jszip.min.js และ lib/docx-preview.min.js และโหลดใน index.html แล้ว');
    }
    // กันข้อมูลที่กรอกในพรีวิวหายโดยไม่รู้ตัว
    if (window.TemplateEditor && TemplateEditor.hasEdits() &&
        !confirm('มีข้อความที่กรอกไว้ในพรีวิว ถ้าโหลดแม่แบบใหม่ ข้อมูลที่กรอกจะหายทั้งหมด\nต้องการดำเนินการต่อหรือไม่?')) {
        return;
    }
    const section = document.getElementById('templatePreviewSection');
    const host = document.getElementById('templatePreview');
    host.innerHTML = '';
    const buf = await loadTemplateBuffer(tpl);
    await docx.renderAsync(buf, host, null, {
        className: 'docx', inWrapper: true, breakPages: true,
        ignoreWidth: false, ignoreHeight: false, renderHeaders: true, renderFooters: true,
    });
    currentTemplate = tpl;
    currentTemplateBuffer = buf;
    document.getElementById('templatePreviewTitle').textContent = 'พรีวิว: ' + tpl.title;
    section.style.display = 'block';
    // เปิดให้กรอกเฉพาะช่องที่ต้องกรอก (ต้องทำหลังแสดง section เพื่อวัดขนาดช่องตารางได้)
    if (window.TemplateEditor) {
        TemplateEditor.enable(host, { lang: tpl.id.endsWith('_en') ? 'en' : 'th' });
    }
    section.scrollIntoView({ behavior: 'smooth' });
}

/** Download the ORIGINAL template bytes (unmodified). */
function downloadCurrentTemplate() {
    if (!currentTemplate || !currentTemplateBuffer) return;
    const blob = new Blob([currentTemplateBuffer],
        { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = currentTemplate.downloadName;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}