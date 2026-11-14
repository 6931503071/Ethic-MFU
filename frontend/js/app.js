/**
 * Main Application Logic
 * Handles UI interactions and document generation workflow
 */

let uploadedFile = null;
let generatedData = null;
let currentPrototypeIndex = 0;

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    initializeUploadArea();
    checkAPIHealth();
});

/**
 * Initialize drag-and-drop upload area
 */
function initializeUploadArea() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Highlight drop area when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.style.borderColor = '#3b82f6';
            uploadArea.style.backgroundColor = '#f0f7ff';
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.style.borderColor = '#e5e7eb';
            uploadArea.style.backgroundColor = '#ffffff';
        }, false);
    });

    // Handle dropped files
    uploadArea.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFileSelect(files[0]);
    }, false);

    // Handle file input change
    fileInput.addEventListener('change', (e) => {
        handleFileSelect(e.target.files[0]);
    });
}

/**
 * Handle file selection
 * @param {File} file - The selected file
 */
function handleFileSelect(file) {
    if (!file) return;

    // Validate file type
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    if (!validTypes.includes(file.type)) {
        showError('❌ ไฟล์ไม่รองรับ โปรดใช้ PDF, DOCX หรือ TXT');
        return;
    }

    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        showError('❌ ไฟล์ใหญ่เกินไป (สูงสุด 10MB)');
        return;
    }

    uploadedFile = file;
    displayFileInfo(file);
    console.log('✅ ไฟล์ที่เลือก:', file.name);
}

/**
 * Display file information
 * @param {File} file - The selected file
 */
function displayFileInfo(file) {
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');

    fileName.textContent = file.name;
    fileSize.textContent = (file.size / 1024).toFixed(2);

    fileInfo.style.display = 'block';
}

/**
 * ✅ MAIN FUNCTION: Generate documents by calling API
 * This is the core function that connects to /api/analysis/fill
 */
async function generate() {
    // ============================================
    // VALIDATION
    // ============================================

    if (!uploadedFile) {
        showError('❌ โปรดเลือกเอกสารก่อน');
        return;
    }

    const docCategory = document.getElementById('docCategory').value;
    if (!docCategory) {
        showError('❌ โปรดเลือกหมวดหมู่เอกสาร');
        return;
    }

    // ============================================
    // PREPARATION
    // ============================================

    const outputLanguage = document.getElementById('outputLanguage').value;
    const additionalNotes = document.getElementById('additionalNotes').value;

    console.log('📋 เตรียมส่งข้อมูล:');
    console.log('  - ไฟล์:', uploadedFile.name);
    console.log('  - หมวดหมู่:', docCategory);
    console.log('  - ภาษา:', outputLanguage);

    // ============================================
    // SHOW LOADING STATE
    // ============================================

    showLoading();

    // ============================================
    // CALL API: /api/analysis/fill
    // ============================================

    try {
        console.log('🚀 เรียก API: POST /api/analysis/fill');

        const response = await analyzeDocument(
            uploadedFile,
            docCategory,
            outputLanguage,
            additionalNotes
        );

        console.log('✅ API Response:', response);

        // ============================================
        // HANDLE API RESPONSE
        // ============================================

        generatedData = response;
        displayResults(response);
        hideLoading();

    } catch (error) {
        console.error('❌ API Error:', error.message);
        showError(`API Error: ${error.message}`);
        hideLoading();
    }
}

/**
 * Display results from API response
 * @param {Object} data - The API response data
 */
function displayResults(data) {
    // Show results section
    document.getElementById('resultsSection').style.display = 'block';

    // ============================================
    // DISPLAY ANALYSIS RESULTS
    // ============================================

    const analysisContent = document.getElementById('analysisContent');
    if (data.analysis) {
        const analysis = data.analysis;
        analysisContent.innerHTML = `
            <div class="analysis-card">
                <p><strong>📌 ชนิดเอกสาร:</strong> ${analysis.document_type || 'Unknown'}</p>
                <p><strong>🌐 ภาษา:</strong> ${analysis.language || 'Unknown'}</p>
                <p><strong>📝 สำหรับทำ:</strong> ${analysis.purpose || 'General'}</p>
                <p><strong>✓ สถานะ:</strong> ${analysis.status || 'Complete'}</p>

                ${analysis.errors && analysis.errors.length > 0 ? `
                    <div style="margin-top: 15px; padding: 10px; background-color: #fee2e2; border-radius: 6px;">
                        <strong style="color: #dc2626;">⚠️ ข้อผิดพลาด/ข้อเตือน:</strong>
                        <ul style="margin-top: 8px; margin-left: 20px;">
                            ${analysis.errors.map(err => `<li>${err}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}

                ${analysis.missing_fields && analysis.missing_fields.length > 0 ? `
                    <div style="margin-top: 15px; padding: 10px; background-color: #fef3c7; border-radius: 6px;">
                        <strong style="color: #d97706;">📋 ข้อมูลที่ต้องกรอก:</strong>
                        <ul style="margin-top: 8px; margin-left: 20px;">
                            ${analysis.missing_fields.map(field => `<li>${field}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    }

    // ============================================
    // DISPLAY 4 DOCUMENT PROTOTYPES
    // ============================================

    const prototypesContent = document.getElementById('prototypesContent');
    prototypesContent.innerHTML = '';

    if (data.prototypes && data.prototypes.length > 0) {
        data.prototypes.forEach((prototype, index) => {
            const prototypeDiv = document.createElement('div');
            prototypeDiv.className = `prototype-preview ${index === 0 ? 'active' : ''}`;

            prototypeDiv.innerHTML = `
                <h4>🔹 ${prototype.name || `รูปแบบที่ ${index + 1}`}</h4>
                <p><strong>📌 รายละเอียด:</strong> ${prototype.description || 'N/A'}</p>

                <div style="margin-top: 15px; padding: 15px; background-color: #f3f4f6; border-radius: 6px; font-family: 'Courier New', monospace; overflow-x: auto;">
                    <pre style="white-space: pre-wrap; word-break: break-word;">${escapeHtml(prototype.content || 'No content')}</pre>
                </div>

                ${prototype.highlighted_sections ? `
                    <div style="margin-top: 15px; padding: 10px; background-color: #dbeafe; border-left: 4px solid #3b82f6; border-radius: 4px;">
                        <strong>🔍 ส่วนที่ต้องตรวจสอบ:</strong>
                        <ul style="margin-top: 8px; margin-left: 20px;">
                            ${prototype.highlighted_sections.map(section => `<li>${section}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            `;

            prototypesContent.appendChild(prototypeDiv);
        });
    } else {
        prototypesContent.innerHTML = '<p>❌ ไม่สามารถสร้างต้นแบบได้</p>';
    }

    // Reset prototype index
    currentPrototypeIndex = 0;
    updatePrototypeDisplay();

    // Scroll to results
    document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
}

/**
 * Switch between document prototypes
 * @param {number} index - Prototype index
 */
function switchPrototype(index) {
    currentPrototypeIndex = index;
    updatePrototypeDisplay();
}

/**
 * Update prototype display and tab states
 */
function updatePrototypeDisplay() {
    // Update preview visibility
    const previews = document.querySelectorAll('.prototype-preview');
    previews.forEach((preview, index) => {
        preview.classList.toggle('active', index === currentPrototypeIndex);
    });

    // Update tab button states
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach((tab, index) => {
        tab.classList.toggle('active', index === currentPrototypeIndex);
    });
}

/**
 * Export to DOCX
 */
async function exportToDocx() {
    if (!generatedData) {
        showError('❌ ไม่มีข้อมูลที่จะส่งออก');
        return;
    }

    showLoading();

    try {
        console.log('📥 ส่งออก DOCX...');
        const blob = await exportDocx(generatedData);
        downloadFile(blob, 'document.docx');
        console.log('✅ ส่งออก DOCX สำเร็จ');
    } catch (error) {
        showError(`ข้อผิดพลาดในการส่งออก: ${error.message}`);
    } finally {
        hideLoading();
    }
}

/**
 * Export to PDF
 */
async function exportToPdf() {
    if (!generatedData) {
        showError('❌ ไม่มีข้อมูลที่จะส่งออก');
        return;
    }

    showLoading();

    try {
        console.log('📥 ส่งออก PDF...');
        const blob = await exportPdf(generatedData);
        downloadFile(blob, 'document.pdf');
        console.log('✅ ส่งออก PDF สำเร็จ');
    } catch (error) {
        showError(`ข้อผิดพลาดในการส่งออก: ${error.message}`);
    } finally {
        hideLoading();
    }
}

/**
 * Reset form to initial state
 */
function resetForm() {
    uploadedFile = null;
    generatedData = null;
    currentPrototypeIndex = 0;

    document.getElementById('fileInput').value = '';
    document.getElementById('fileInfo').style.display = 'none';
    document.getElementById('docCategory').value = '';
    document.getElementById('outputLanguage').value = 'en';
    document.getElementById('additionalNotes').value = '';

    hideLoading();
    hideError();
    document.getElementById('resultsSection').style.display = 'none';

    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ============================================
// UI STATE MANAGEMENT
// ============================================

/**
 * Show loading state
 */
function showLoading() {
    document.getElementById('loadingState').style.display = 'block';
    document.getElementById('errorState').style.display = 'none';
    document.getElementById('generateBtn').disabled = true;
}

/**
 * Hide loading state
 */
function hideLoading() {
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('generateBtn').disabled = false;
}

/**
 * Show error message
 * @param {string} message - Error message
 */
function showError(message) {
    const errorState = document.getElementById('errorState');
    const errorMessage = document.getElementById('errorMessage');

    errorMessage.textContent = message;
    errorState.style.display = 'block';
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('generateBtn').disabled = false;

    console.error('🚨 Error:', message);
}

/**
 * Hide error message
 */
function hideError() {
    document.getElementById('errorState').style.display = 'none';
}

// ============================================
// UTILITIES
// ============================================

/**
 * Escape HTML characters
 * @param {string} text - Text to escape
 * @returns {string}
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Check API health
 */
async function checkAPIHealth() {
    const isHealthy = await healthCheck();
    if (!isHealthy) {
        console.warn('⚠️ คำเตือน: ไม่สามารถเชื่อมต่อ API ที่ localhost:8050');
        console.log('📌 โปรดตรวจสอบว่า Backend กำลังทำงาน');
    } else {
        console.log('✅ API พร้อมใช้งาน');
    }
}
