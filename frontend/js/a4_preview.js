/**
 * A4 Template Preview Module
 * Renders AP02 template as A4 preview with auto-filled fields
 */

// ═══════════════════════════════════════════
// TEMPLATE PREVIEW RENDERER
// ═══════════════════════════════════════════

function createA4Preview(data) {
    // Create an A4 preview of the AP02 template with filled data

    const analysis = data.analysis || {};
    const metadata = data.metadata || {};

    // Create A4 container
    const a4 = document.createElement('div');
    a4.style.cssText = `
        width: 100%;
        max-width: 210mm;
        aspect-ratio: 210 / 297;
        padding: 20px;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        font-family: 'Sarabun', 'TH Sarabun New', Arial, sans-serif;
        line-height: 1.6;
        color: #1f2937;
        font-size: 14px;
        overflow: auto;
        margin: 0 auto;
    `;

    // Header
    const header = createHeader(data);
    a4.appendChild(header);

    // Title
    const title = createSection1Title(analysis);
    a4.appendChild(title);

    // Field of Study
    const fieldOfStudy = createSection2FieldOfStudy(analysis);
    a4.appendChild(fieldOfStudy);

    // Team Info (simplified)
    const team = createSection3Team(analysis);
    a4.appendChild(team);

    // Objectives
    const objectives = createSection4Objectives(analysis);
    a4.appendChild(objectives);

    // Footer
    const footer = createFooter();
    a4.appendChild(footer);

    return a4;
}

function createHeader(data) {
    const header = document.createElement('div');
    header.style.cssText = `
        display: flex;
        justify-content: space-between;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 1px solid #d1d5db;
    `;

    const left = document.createElement('span');
    left.textContent = 'Version......  Date........................';
    left.style.fontSize = '12pt';

    const right = document.createElement('span');
    right.textContent = 'AP 02/2026';
    right.style.fontSize = '12pt';
    right.style.fontWeight = 'bold';

    header.appendChild(left);
    header.appendChild(right);
    return header;
}

function createSection1Title(analysis) {
    const section = document.createElement('div');
    section.style.cssText = 'margin-bottom: 20px;';

    const title = document.createElement('h2');
    title.textContent = '1. ชื่อโครงการวิจัย (Title)';
    title.style.cssText = 'font-size: 18pt; font-weight: bold; margin: 0 0 10px 0;';

    const thTitle = document.createElement('p');
    thTitle.innerHTML = `<strong>(ชื่อภาษาไทย):</strong> <span style="color: #dc2626;">${
        analysis.missing_fields?.length > 0 ? '[กรุณากรอกชื่อโครงการวิจัยภาษาไทย]' : 'กรอกข้อมูล'
    }</span>`;
    thTitle.style.margin = '8px 0';

    const enTitle = document.createElement('p');
    enTitle.innerHTML = `<strong>(ชื่อภาษาอังกฤษ):</strong> <span style="color: #dc2626;">${
        analysis.missing_fields?.length > 0 ? '[Please enter research title in English]' : 'Enter data'
    }</span>`;
    enTitle.style.margin = '8px 0';

    section.appendChild(title);
    section.appendChild(thTitle);
    section.appendChild(enTitle);
    return section;
}

function createSection2FieldOfStudy(analysis) {
    const section = document.createElement('div');
    section.style.cssText = 'margin-bottom: 20px;';

    const title = document.createElement('h2');
    title.textContent = '2. สาขาวิชาที่ทำการวิจัย (Field of Research)';
    title.style.cssText = 'font-size: 18pt; font-weight: bold; margin: 0 0 10px 0;';

    const field = document.createElement('p');
    field.innerHTML = `<strong>สาขาวิชา:</strong> <span style="color: #f59e0b;">แพทยศาสตร์</span>
    <br><em style="font-size: 13pt; color: #6b7280;">เช่น แพทยศาสตร์ ทันตแพทยศาสตร์ สาธารณสุขศาสตร์ เป็นต้น</em>`;
    field.style.margin = '8px 0';

    section.appendChild(title);
    section.appendChild(field);
    return section;
}

function createSection3Team(analysis) {
    const section = document.createElement('div');
    section.style.cssText = 'margin-bottom: 20px;';

    const title = document.createElement('h2');
    title.textContent = '3. ผู้วิจัย ผู้วิจัยร่วม และที่ปรึกษา';
    title.style.cssText = 'font-size: 18pt; font-weight: bold; margin: 0 0 10px 0;';

    const piTitle = document.createElement('h3');
    piTitle.textContent = '3.1 ผู้วิจัยหลัก (Principal Investigator)';
    piTitle.style.cssText = 'font-size: 14pt; font-weight: bold; margin: 10px 0 8px 0;';

    const fields = [
        { label: 'ตำแหน่งวิชาการ-ชื่อ-สกุล', value: '[กรุณากรอก]', color: '#dc2626' },
        { label: 'สาขาวิชา/หน่วยงาน', value: '[กรุณากรอก]', color: '#dc2626' },
        { label: 'ที่อยู่', value: '[กรุณากรอก]', color: '#dc2626' },
        { label: 'เบอร์โทร/อีเมล', value: '[กรุณากรอก]', color: '#dc2626' }
    ];

    section.appendChild(title);
    section.appendChild(piTitle);

    fields.forEach(f => {
        const p = document.createElement('p');
        p.innerHTML = `<strong>${f.label}:</strong> <span style="color: ${f.color};">${f.value}</span>`;
        p.style.margin = '6px 0';
        section.appendChild(p);
    });

    return section;
}

function createSection4Objectives(analysis) {
    const section = document.createElement('div');
    section.style.cssText = 'margin-bottom: 20px;';

    const title = document.createElement('h2');
    title.textContent = '4. วัตถุประสงค์ของการวิจัย (Research Objectives)';
    title.style.cssText = 'font-size: 18pt; font-weight: bold; margin: 0 0 10px 0;';

    const obj = document.createElement('p');
    obj.innerHTML = `<span style="color: #f59e0b;">วัตถุประสงค์ของการวิจัย...</span>
    <br><em style="font-size: 13pt; color: #6b7280; display: block; margin-top: 8px;">
    [ระบุวัตถุประสงค์ของการวิจัยอย่างชัดเจน]
    </em>`;
    obj.style.margin = '8px 0';

    section.appendChild(title);
    section.appendChild(obj);
    return section;
}

function createFooter() {
    const footer = document.createElement('div');
    footer.style.cssText = `
        margin-top: 40px;
        padding-top: 10px;
        border-top: 1px solid #d1d5db;
        text-align: center;
        font-size: 12pt;
        color: #6b7280;
    `;

    footer.textContent = 'หน้า 1 จาก 1';
    return footer;
}

// ═══════════════════════════════════════════
// INTEGRATION WITH RESULTS
// ═══════════════════════════════════════════

function addA4PreviewToResults(data) {
    // Add A4 preview window to the results section

    const resultsSection = document.getElementById('resultsSection');
    if (!resultsSection) return;

    // Create preview container
    const previewContainer = document.createElement('div');
    previewContainer.id = 'a4PreviewContainer';
    previewContainer.style.cssText = `
        background: #f3f4f6;
        border-radius: 8px;
        padding: 20px;
        margin: 20px 0;
        overflow-y: auto;
        max-height: 600px;
    `;

    const previewLabel = document.createElement('h3');
    previewLabel.textContent = '📄 A4 Template Preview (AP 02/2026)';
    previewLabel.style.cssText = 'font-size: 16px; margin: 0 0 16px 0; color: #1f2937;';

    previewContainer.appendChild(previewLabel);

    // Create A4 preview
    const a4Preview = createA4Preview(data);
    previewContainer.appendChild(a4Preview);

    // Insert before prototypes (fix: find the actual tabs element)
    const protoTabs = resultsSection.querySelector('#protoTabs');

    if (protoTabs) {
        // Insert before the proto tabs
        resultsSection.insertBefore(previewContainer, protoTabs);
    } else {
        // Fallback: insert before field status section
        const fieldStatus = resultsSection.querySelector('#fieldStatusSection');
        if (fieldStatus && fieldStatus.nextElementSibling) {
            resultsSection.insertBefore(previewContainer, fieldStatus.nextElementSibling);
        } else {
            // Last resort: append at the end
            resultsSection.appendChild(previewContainer);
        }
    }
}
