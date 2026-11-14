/**
 * API Client Module
 * Handles all API communication with the backend
 */

const API_BASE_URL = 'http://localhost:8050'; // ✅ เปลี่ยนตามต้องการ

// ============================================
// MOCK MODE — ใช้เมื่อ Backend ยังไม่รัน
// ตั้งค่าเป็น false เมื่อ Backend พร้อม
// ============================================
const USE_MOCK = false;

/**
 * Send file to API for analysis
 * @param {File} file - The uploaded file
 * @param {string} category - Document category
 * @param {string} language - Output language (en/th/both)
 * @param {string} notes - Additional notes from user
 * @returns {Promise<Object>} API response
 */
async function analyzeDocument(file, category, language, notes) {

    // ── MOCK MODE ────────────────────────────────
    if (USE_MOCK) {
        console.log('⚠️ MOCK MODE: ใช้ข้อมูลจำลอง (Backend ยังไม่รัน)');
        await new Promise(r => setTimeout(r, 1500)); // simulate delay
        return buildMockResponse(file, category, language);
    }

    // ── REAL API ─────────────────────────────────
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category);
    formData.append('language', language);
    formData.append('notes', notes);

    try {
        const response = await fetch(`${API_BASE_URL}/api/analysis/fill`, {
            method: 'POST',
            body: formData,
            // ⚠️ DO NOT set Content-Type header - browser will set it automatically with boundary
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `API Error: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        // ── Friendly error messages ───────────────
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            throw new Error(
                'ไม่สามารถเชื่อมต่อ Backend ได้\n\n' +
                'วิธีแก้:\n' +
                '1. เปิด terminal ใหม่\n' +
                '2. ไปที่โฟลเดอร์ backend\n' +
                '3. รัน: python standalone_server.py\n' +
                '4. รอให้เห็น "Ready to accept requests..."\n' +
                '5. กลับมากด "สร้างเอกสาร" อีกครั้ง'
            );
        }
        console.error('❌ API Error:', error);
        throw error;
    }
}

/**
 * Build mock response for UI testing (no backend needed)
 */
function buildMockResponse(file, category, language) {
    const isThai = language === 'th';
    const catLabel = {
        research_proposal: 'Research Proposal (AP 02/2026)',
        ethics_submission: 'Ethics Submission Document',
        general: 'General Document',
        administrative: 'Administrative Document'
    }[category] || 'Document';

    const sampleText = `[ตัวอย่างเนื้อหาจากไฟล์ "${file.name}"]\n\nThis is a mock document generated for UI testing. The actual content would be extracted from the uploaded file by the backend.\n\nResearch Title: [PLEASE ENTER RESEARCH TITLE]\nResearcher: [PLEASE ENTER RESEARCHER NAME]\nInstitution: Mae Fah Luang University\nDate: [PLEASE ENTER DATE]`;

    return {
        analysis: {
            document_type: catLabel,
            language: isThai ? 'th' : 'en',
            purpose: 'Research Ethics Committee Submission',
            status: 'Complete',
            word_count: 42,
            page_estimate: 1,
            errors: ['⚠️ นี่คือข้อมูลจำลอง (MOCK MODE) — รัน Backend เพื่อวิเคราะห์ไฟล์จริง'],
            missing_fields: [
                '[PLEASE ENTER RESEARCHER NAME]',
                '[PLEASE ENTER RESEARCH TITLE]',
                '[PLEASE ENTER ETHICS APPROVAL NUMBER]',
                '[PLEASE ENTER PROJECT DATES]'
            ]
        },
        prototypes: [
            {
                name: isThai ? 'รูปแบบการเขียนวิชาการ' : 'Formal Academic Style',
                description: isThai ? 'สไตล์การเขียนอย่างเป็นทางการ' : 'Comprehensive academic approach with formal terminology',
                style: 'academic',
                content: sampleText,
                highlighted_sections: ['Introduction', 'Methodology', 'Expected Outcomes'],
                notes: 'Use this version for formal submissions to ethics committees'
            },
            {
                name: isThai ? 'รูปแบบธุรกิจ' : 'Concise Business Style',
                description: isThai ? 'สไตล์การเขียนกระชับและชัดเจน' : 'Direct and focused presentation',
                style: 'business',
                content: sampleText,
                highlighted_sections: ['Objectives', 'Methods'],
                notes: 'Use this version for executive summaries'
            },
            {
                name: isThai ? 'รูปแบบการบรรยาย' : 'Narrative Detailed Style',
                description: isThai ? 'สไตล์การบรรยายรายละเอียด' : 'Story-like presentation with comprehensive explanations',
                style: 'narrative',
                content: sampleText,
                highlighted_sections: ['Background', 'Discussion'],
                notes: 'Use this version for detailed reports'
            },
            {
                name: isThai ? 'รูปแบบโครงสร้างมาตรฐาน' : 'Structured Template Style',
                description: isThai ? 'สไตล์ที่มีโครงสร้างชัดเจน' : 'Organized format with clear sections',
                style: 'structured',
                content: sampleText,
                highlighted_sections: ['Overview', 'Key Points', 'Next Steps'],
                notes: 'Use this version for easy review and modification'
            }
        ],
        metadata: {
            file_name: file.name,
            file_size: file.size,
            category: category,
            language: language,
            mock: true
        }
    };
}

/**
 * Export document to DOCX
 * @param {Object} documentData - The document content
 * @returns {Promise<Blob>} DOCX file blob
 */
async function exportDocx(documentData) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/export/docx`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(documentData),
        });

        if (!response.ok) {
            throw new Error(`Export Error: ${response.status}`);
        }

        return await response.blob();
    } catch (error) {
        console.error('❌ Export Error:', error);
        throw error;
    }
}

/**
 * Export document to PDF
 * @param {Object} documentData - The document content
 * @returns {Promise<Blob>} PDF file blob
 */
async function exportPdf(documentData) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/export/pdf`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(documentData),
        });

        if (!response.ok) {
            throw new Error(`Export Error: ${response.status}`);
        }

        return await response.blob();
    } catch (error) {
        console.error('❌ Export Error:', error);
        throw error;
    }
}

/**
 * Trigger download for a blob file
 * @param {Blob} blob - The file blob
 * @param {string} filename - The filename
 */
function downloadFile(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
}

/**
 * Health check - verify API is running
 * @returns {Promise<boolean>}
 */
async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
        });
        return response.ok;
    } catch (error) {
        console.warn('⚠️ API is not accessible at', API_BASE_URL);
        return false;
    }
}
