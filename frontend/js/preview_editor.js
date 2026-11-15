/**
 * preview_editor.js — กรอกข้อมูลในพรีวิวแม่แบบ (docx-preview)
 * ---------------------------------------------------------------
 * หลักการ
 *  - หัวข้อ/ป้ายชื่อของฟอร์ม "ล็อก" แก้ไม่ได้
 *  - ช่องที่ต้องกรอกเปิดให้พิมพ์ได้ และเป็น "ตัวหนังสือสีแดง" จนกว่าจะกรอก
 *  - กรอกแล้วตัวหนังสือเปลี่ยนเป็นสีดำ (เห็นทันทีว่าเหลือช่องไหนบ้าง)
 *
 * ช่องกรอกถูกตรวจจับอัตโนมัติจาก 6 กฎ (แก้ค่าได้ที่ CFG ด้านล่าง)
 *  A. ข้อความสีน้ำเงิน = ข้อความแนะนำของฟอร์ม (guide) → แทนที่ด้วยข้อมูลจริง
 *  D. ข้อความในวงเล็บทั้งช่อง เช่น "(ชื่อภาษาไทย)" ในตาราง (ph)
 *  E. หมายเลขข้อ เช่น "1." "2." → เปิดช่องให้พิมพ์ต่อท้ายเลข (item)
 *  C. ข้อความจุดไข่ปลา เช่น "ระบุ ......", "เดือน... พ.ศ. ...", "นาย…" (ph)
 *  B. ช่องตารางที่ว่างและกว้างพอ (cell)  ← ช่องแคบ เช่น ช่องเดือนใน Gantt ไม่นับ
 *  ส่วนหัว/ท้ายกระดาษ (Version / Date / เลขหน้า) ไม่ถูกเปิดให้แก้
 *
 * ข้อจำกัดปัจจุบัน
 *  - ข้อความที่กรอกอยู่ "ในพรีวิวเท่านั้น" ยังไม่ถูกเขียนกลับลงไฟล์ DOCX
 *  - ช่องติ๊กเลือก (checkbox) ยังไม่รองรับ
 */
(function (global) {
    'use strict';

    const CFG = {
        minCellWidth: 60,    // px — ช่องว่างที่แคบกว่านี้ถือเป็นช่องจัดหน้า ไม่ใช่ช่องกรอก
        minCellHeight: 14,   // px
        maxPlaceholderLen: 40,
        maxParenLen: 80,
        hints: { th: 'กรอกข้อมูล…', en: 'Enter text…' },
    };

    const STYLE_ID = 'tpl-editor-style';
    const CSS = `
    .fill-field{outline:1px dashed rgba(220,38,38,.55);outline-offset:1px;border-radius:2px;cursor:text}
    span.fill-field[data-empty="true"]{display:inline-block;min-width:4em}
    .fill-field[data-fill="item"]{margin-left:.4em}
    .fill-field[data-state="todo"],.fill-field[data-state="todo"] *{color:#dc2626 !important}
    .fill-field[data-state="todo"]{background:rgba(220,38,38,.07)}
    .fill-field[data-state="done"],.fill-field[data-state="done"] *{color:#000 !important}
    .fill-field[data-state="done"]{outline:1px dotted rgba(22,163,74,.55);background:transparent}
    .fill-field:focus{outline:2px solid #3b82f6;background:#eff6ff}

    .fill-field,.fill-field *,.fill-field[data-empty="true"]::before{
        font-family:'TH Sarabun New',sans-serif !important;
        font-size:16pt !important;
        font-weight:normal !important;
        font-style:normal !important;
    }
    .fill-field[data-empty="true"]::before{content:attr(data-hint);color:#dc2626;opacity:.75;pointer-events:none}
    #tplEditBar{position:sticky;top:0;z-index:5;display:flex;align-items:center;gap:12px;flex-wrap:wrap;
        background:#fff7ed;border:1px solid #fdba74;border-radius:8px;padding:8px 12px;margin-bottom:10px;font-size:14px}
    #tplEditBar .bar-count{flex:1;min-width:180px;color:#7c2d12}
    #tplEditBar.all-done{background:#ecfdf5;border-color:#6ee7b7}
    #tplEditBar.all-done .bar-count{color:#065f46}
    #tplEditBar button{border:1px solid #e5e7eb;background:#fff;border-radius:6px;padding:6px 14px;cursor:pointer;font-size:13px}
    #tplEditBar button:hover{background:#f3f4f6}
    `;

    let host = null;
    let bar = null;
    let fields = [];
    let hint = CFG.hints.th;

    // ───────────── helpers ─────────────
    const norm = s => String(s).replace(/[\u00a0\u200b]/g, ' ').replace(/\s+/g, ' ').trim();

    function injectStyle() {
        if (document.getElementById(STYLE_ID)) return;
        const st = document.createElement('style');
        st.id = STYLE_ID;
        st.textContent = CSS;
        document.head.appendChild(st);
    }

    function isBlue(el) {
        const m = getComputedStyle(el).color.match(/\d+(\.\d+)?/g);
        if (!m) return false;
        const r = +m[0], g = +m[1], b = +m[2];
        return b >= 140 && b - r >= 50 && b - g >= 15;
    }

    function textNodesOf(root) {
        const out = [];
        const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        while (w.nextNode()) out.push(w.currentNode);
        return out;
    }

    function inField(node) {
        const el = node.nodeType === 1 ? node : node.parentElement;
        return !!(el && el.closest('.fill-field'));
    }

    // ───────────── field model ─────────────
    function makeField(el, type) {
        if (el.classList.contains('fill-field')) return null;
        el.classList.add('fill-field');
        el.dataset.fill = type;
        el.dataset.orig = type === 'cell' || type === 'item' ? '' : norm(el.textContent);
        el.dataset.hint = hint;
        el.contentEditable = 'true';
        el.spellcheck = false;
        el.setAttribute('role', 'textbox');
        fields.push(el);
        refresh(el);
        return el;
    }

    function refresh(el) {
        const t = norm(el.textContent);
        const unchanged = t === el.dataset.orig;
        const todo = t === '' || unchanged;
        el.dataset.state = todo ? 'todo' : 'done';
        el.dataset.empty = t === '' ? 'true' : 'false';
    }

    // ───────────── detection rules ─────────────
    function ruleGuidance(root) {            // A
        root.querySelectorAll('p').forEach(p => {
            if (inField(p)) return;
            const kids = Array.from(p.children);
            const runs = kids.filter(k => norm(k.textContent) !== '');
            if (!runs.length) return;
            const blue = runs.map(isBlue);
            if (blue.every(Boolean)) { makeField(p, 'guide'); return; }
            if (!blue.some(Boolean)) return;
            let group = [];
            const flush = () => {
                if (!group.length) return;
                const w = document.createElement('span');
                group[0].before(w);
                group.forEach(g => w.appendChild(g));
                makeField(w, 'guide');
                group = [];
            };
            kids.forEach(k => {
                if (norm(k.textContent) === '') { if (group.length) group.push(k); return; }
                if (isBlue(k)) group.push(k); else flush();
            });
            flush();
        });
    }

    function ruleParenCells(root) {          // D
        root.querySelectorAll('td p').forEach(p => {
            if (inField(p)) return;
            const t = norm(p.textContent);
            if (t.length >= 3 && t.length <= CFG.maxParenLen && /^[(（].*[)）]$/.test(t)) makeField(p, 'ph');
        });
    }

    function ruleListMarkers(root) {         // E
        root.querySelectorAll('p').forEach(p => {
            if (inField(p)) return;
            if (!/^\d{1,2}[.)]$/.test(norm(p.textContent))) return;
            const s = document.createElement('span');
            s.textContent = '';
            p.appendChild(s);
            makeField(s, 'item');
        });
    }

    function isWholePlaceholder(t) {
        t = norm(t);
        if (!t || t.length > CFG.maxPlaceholderLen) return false;
        if (/^(ระบุข้อมูล|specify)$/i.test(t)) return true;
        if (!/…|\.{3,}|_{3,}/.test(t)) return false;
        const rest = t
            .replace(/ระบุข้อมูล|ระบุ|specify|อธิบายรายละเอียด|describe in detail|describe details|describe|นางสาว|นาง|นาย|mrs\.?|mr\.?|ms\.?/gi, '')
            .replace(/[\s.…_\-—()/]/g, '');
        return rest === '';
    }

    function rulePlaceholders(root) {        // C
        textNodesOf(root).forEach(n => {
            if (inField(n)) return;
            const t = n.nodeValue;
            if (!norm(t)) return;
            if (isWholePlaceholder(t)) {
                const s = document.createElement('span');
                n.parentNode.replaceChild(s, n);
                s.appendChild(n);
                makeField(s, 'ph');
                return;
            }
            const re = /(?:…|\.{3,}|_{3,})+/g;
            if (!re.test(t)) return;
            re.lastIndex = 0;
            const frag = document.createDocumentFragment();
            const made = [];
            let last = 0, m;
            while ((m = re.exec(t))) {
                if (m.index > last) frag.appendChild(document.createTextNode(t.slice(last, m.index)));
                const s = document.createElement('span');
                s.textContent = m[0];
                frag.appendChild(s);
                made.push(s);
                last = m.index + m[0].length;
            }
            if (last < t.length) frag.appendChild(document.createTextNode(t.slice(last)));
            n.parentNode.replaceChild(frag, n);
            made.forEach(s => makeField(s, 'ph'));
        });
    }

    function ruleEmptyCells(root) {          // B
        root.querySelectorAll('td').forEach(td => {
            if (td.querySelector('table,img,.fill-field') || td.closest('.fill-field')) return;
            if (norm(td.textContent) !== '') return;
            const r = td.getBoundingClientRect();
            if (r.width < CFG.minCellWidth || r.height < CFG.minCellHeight) return;
            const tbl = td.closest('table');
            if (!tbl || norm(tbl.textContent) === '') return;
            makeField(td.querySelector('p') || td, 'cell');
        });
    }

    // ───────────── status bar ─────────────
    function ensureBar() {
        if (bar && bar.isConnected) return;
        bar = document.createElement('div');
        bar.id = 'tplEditBar';
        bar.innerHTML =
            '<span class="bar-count"></span>' +
            '<button type="button" data-act="next">ช่องถัดไปที่ยังไม่กรอก ▶</button>';
        host.parentNode.insertBefore(bar, host);
        bar.querySelector('[data-act="next"]').addEventListener('click', goNext);
    }

    function updateBar() {
        if (!bar) return;
        const total = fields.length;
        const todo = fields.filter(f => f.dataset.state === 'todo').length;
        const done = total - todo;
        bar.classList.toggle('all-done', total > 0 && todo === 0);
        bar.querySelector('.bar-count').textContent = total === 0
            ? 'ไม่พบช่องที่ต้องกรอกในแม่แบบนี้'
            : todo === 0
                ? `✓ กรอกครบทุกช่องแล้ว (${total} ช่อง)`
                : `ช่องสีแดง = ยังไม่กรอก · กรอกแล้ว ${done}/${total} ช่อง (เหลือ ${todo})`;
        const btn = bar.querySelector('[data-act="next"]');
        btn.style.display = todo === 0 ? 'none' : '';
    }

    function goNext() {
        if (!fields.length) return;
        const cur = document.activeElement && document.activeElement.closest
            ? document.activeElement.closest('.fill-field') : null;
        const start = cur ? fields.indexOf(cur) + 1 : 0;
        for (let i = 0; i < fields.length; i++) {
            const el = fields[(start + i) % fields.length];
            if (el.dataset.state === 'todo') {
                el.scrollIntoView({ block: 'center', behavior: 'smooth' });
                el.focus({ preventScroll: true });
                return;
            }
        }
    }

    // ช่องที่ยังเป็นข้อความตัวอย่าง → เลือกทั้งหมดก่อน เพื่อให้สิ่งที่พิมพ์/วางแทนที่ข้อความตัวอย่าง
    function selectIfPlaceholder(f) {
        if (!f || f.dataset.state !== 'todo' || f.dataset.empty === 'true') return;
        const r = document.createRange();
        r.selectNodeContents(f);
        const s = getSelection();
        s.removeAllRanges();
        s.addRange(r);
    }

    // ───────────── events (bound once per host) ─────────────
    function fieldOf(e) {
        return e.target && e.target.closest ? e.target.closest('.fill-field') : null;
    }

    function bindEvents() {
        if (host._tplEditorBound) return;
        host._tplEditorBound = true;

        host.addEventListener('input', e => {
            const f = fieldOf(e);
            if (!f) return;
            refresh(f);
            updateBar();
        });

        // ช่องที่ยังเป็นข้อความตัวอย่าง: ตัวอักษรแรกที่พิมพ์/วาง จะแทนที่ข้อความตัวอย่างทั้งหมด
        // (ทำใน beforeinput เพื่อไม่ให้เกิดการแข่งกับการพิมพ์เร็ว)
        host.addEventListener('beforeinput', e => {
            if (/^(insertText|insertFromPaste|insertCompositionText|deleteContent|deleteByCut)/.test(e.inputType)) {
                selectIfPlaceholder(fieldOf(e));
            }
        });

        host.addEventListener('keydown', e => {
            const f = fieldOf(e);
            if (!f || e.key !== 'Enter') return;
            e.preventDefault();
            const multi = f.dataset.fill === 'cell' || f.dataset.fill === 'guide';
            if (multi) document.execCommand('insertLineBreak');
        });

        host.addEventListener('paste', e => {
            const f = fieldOf(e);
            if (!f) return;
            e.preventDefault();
            selectIfPlaceholder(f);
            let t = (e.clipboardData || global.clipboardData).getData('text/plain') || '';
            if (!(f.dataset.fill === 'cell' || f.dataset.fill === 'guide')) t = t.replace(/\s*\n\s*/g, ' ');
            document.execCommand('insertText', false, t);
        });

        host.addEventListener('drop', e => e.preventDefault());
    }

    // ───────────── public API ─────────────
    function enable(hostEl, opts) {
        injectStyle();
        host = hostEl;
        fields = [];
        hint = (opts && opts.lang === 'en') ? CFG.hints.en : CFG.hints.th;

        const roots = host.querySelectorAll('article');
        const list = roots.length ? Array.from(roots) : [host];
        list.forEach(r => {
            ruleGuidance(r);
            ruleParenCells(r);
            ruleListMarkers(r);
            rulePlaceholders(r);
            ruleEmptyCells(r);
        });

        fields.sort((a, b) => (a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1));
        ensureBar();
        bindEvents();
        updateBar();
        return fields.length;
    }

    function hasEdits() { return fields.some(f => f.dataset.state === 'done'); }

    /** ค่าที่กรอก (สำหรับขั้นถัดไป: เขียนกลับลง DOCX) */
    function getValues() {
        return fields.map((f, i) => ({
            index: i, type: f.dataset.fill, original: f.dataset.orig,
            value: norm(f.textContent), filled: f.dataset.state === 'done',
        }));
    }

    global.TemplateEditor = { enable, hasEdits, getValues };

    window.addEventListener('beforeunload', e => {
        if (hasEdits()) { e.preventDefault(); e.returnValue = ''; }
    });
})(window);