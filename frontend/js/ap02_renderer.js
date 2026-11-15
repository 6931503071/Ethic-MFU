/**
 * ap02_renderer.js — วาดแบบฟอร์ม AP 02/2026 จาก templates/ap02.json  (ขั้นที่ 1 จาก 4)
 * -----------------------------------------------------------------------------------
 * ขั้นนี้ทำ: อ่าน JSON แล้ววาดฟอร์มทั้งฉบับ (ไทย/อังกฤษ) เป็นหน้ากระดาษกว้าง 210 mm หนึ่งแผ่นยาว
 *   - หัวกระดาษ: Version .... Date .... (ซ้าย, พิมพ์แก้ได้)   AP 02/2026 (ขวา)
 *   - หัวข้อทุกระดับ 18 pt / เนื้อหา 16 pt / ไม่มีตัวหนา (บังคับด้วย CSS)
 *   - ช่องกรอกเป็นสีแดงจนกว่าจะพิมพ์ แล้วเปลี่ยนเป็นสีดำ
 *   - ช่องติ๊ก ☐ กดแล้วเป็น ☑ (radio เลือกได้ข้อเดียวต่อกลุ่ม)
 *   - ตอบ "ไม่ใช่" ในหัวข้อ 12.2 A-G แล้วเนื้อหาส่วนนั้นถูกซ่อน
 *   - รายการข้อ 1. 2. 3. แสดงตามจำนวน min_items ใน JSON (11.4-11.7 = 3 ข้อ)
 *
 * ขั้นนี้ยังไม่ทำ (ทำในขั้นถัดไป):
 *   - แบ่งเป็นหน้า A4 หลายหน้าและท้ายกระดาษ "หน้า X จาก Y"   (ขั้นที่ 2)
 *   - ปุ่ม "+ เพิ่มข้อ" / ลบข้อ และเก็บค่าที่กรอกเป็นก้อนเดียว (ขั้นที่ 3)
 *   - ส่งออก DOCX / PDF                                      (ขั้นที่ 4)
 *
 * ทุกชิ้นที่ขั้นที่ 2 ต้องใช้แบ่งหน้า มี class "blk" ติดไว้แล้ว
 *
 * ใช้งาน:  Ap02Renderer.show(hostElement, 'th' | 'en')
 */
(function (global) {
    'use strict';

    const DEFAULT_URL = 'templates/ap02.json';
    const STYLE_ID = 'ap02-render-style';
    const ON = '\u2611';   // ☑
    const OFF = '\u2610';  // ☐

    const DETAIL_RX = /ระบุ|อธิบายรายละเอียด|specify|describe/i;
    const NO_DETAIL_RX = /กระดาษ|paper/i;

    const CSS = `
    .ap02-doc{--b:16pt;--h:18pt;font-family:'TH Sarabun New','Sarabun','Noto Sans Thai',Tahoma,sans-serif;
    font-size:var(--b);line-height:1.25;color:#000}
    .ap02-doc,.ap02-doc *{font-weight:normal !important;font-style:normal !important;box-sizing:border-box}
    .ap02-doc [hidden]{display:none !important}
    .ap02-doc.no-hints .guide{display:none}

    .ap02-flow{width:210mm;margin:0 auto 14px;padding:25.4mm 24.9mm 20mm;background:#fff;
    box-shadow:0 2px 8px rgba(0,0,0,.25)}
    .ap02-doc .hdr{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:5mm}
    .ap02-doc .doc-title{font-size:var(--h);text-align:center;margin:0 0 5mm}

    .ap02-doc .h{font-size:var(--h);line-height:1.2}
    .ap02-doc div.h{margin:6mm 0 2mm}
    .ap02-doc div.h.l1{margin-top:4mm}
    .ap02-doc div.h.l2{margin-top:3mm}
    .ap02-doc .lbl{margin:1mm 0}
    .ap02-doc .hint{color:#1d4ed8;margin:0 0 1.5mm}

    .ap02-doc .ph{display:inline-block;min-width:5em;color:#dc2626;background:rgba(220,38,38,.07);
        border-bottom:1px dashed #dc2626;outline:none;cursor:text}
    .ap02-doc .ph:empty::before{content:attr(data-hint);opacity:.8}
    .ap02-doc .ph:focus{outline:2px solid #3b82f6;background:#eff6ff}
    .ap02-doc .ph.ml{display:block;min-height:3.2em;white-space:pre-wrap;margin:0 0 2mm}
    .ap02-doc .ph.filled{color:#000;background:transparent;border-bottom-color:transparent}

    .ap02-doc .li{display:flex;gap:2mm;margin:0 0 1mm}
    .ap02-doc .li .no{flex:0 0 8mm}
    .ap02-doc .li .ph{flex:1;display:block;min-width:0}

    .ap02-doc .opt{display:flex;gap:2mm;align-items:flex-start;margin:0 0 1mm;padding-left:3mm}
    .ap02-doc .opt .tx{flex:1}
    .ap02-doc .cb{flex:0 0 auto;cursor:pointer;user-select:none;line-height:1.2;
        font-family:'Segoe UI Symbol','Noto Sans Symbols 2','Arial Unicode MS',sans-serif}
    .ap02-doc .cb:focus{outline:2px solid #3b82f6}

    .ap02-doc table.dt{width:100%;border-collapse:collapse;margin:0 0 3mm}
    .ap02-doc .dt th,.ap02-doc .dt td{border:1px solid #000;padding:1mm 2mm;vertical-align:top;text-align:left}
    .ap02-doc .dt th{background:#e5e7eb}
    .ap02-doc .dt th.red{color:#dc2626}
    .ap02-doc .dt .ctr{text-align:center}
    .ap02-doc .dt td.k{background:#e5e7eb;width:36%}
    .ap02-doc .dt td.h{margin:0}
    .ap02-doc .dt td .opt{padding-left:0}
    .ap02-doc .dt td.cell{height:9mm;outline:none}
    .ap02-doc .dt td.cell:empty{background:rgba(220,38,38,.07)}
    .ap02-doc .dt td.cell:focus{background:#eff6ff}
    .ap02-doc .dt .no{margin-right:2mm}
    .ap02-doc .gantt{table-layout:fixed}
    .ap02-doc .gantt td.cell:empty{background:transparent}
    .ap02-doc .gate td.k{width:40%}
    `;

  // ---------------------------------------------------------------- helpers
    const el = (tag, cls, text) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
    };
    const pick = (o, k, lang) => (lang === 'en' && o[k + '_en'] != null) ? o[k + '_en'] : o[k];
    const blk = n => { n.classList.add('blk'); return n; };

    function injectStyle() {
        if (document.getElementById(STYLE_ID)) return;
        const st = document.createElement('style');
        st.id = STYLE_ID;
        st.textContent = CSS;
        document.head.appendChild(st);
    }

    /** ช่องกรอก (แดงจนกว่าจะพิมพ์) */
    function ph(key, ctx, opts) {
        opts = opts || {};
        const s = el('span', 'ph' + (opts.multiline ? ' ml' : ''));
        s.contentEditable = 'true';
        s.spellcheck = false;
        s.setAttribute('role', 'textbox');
        s.dataset.key = key;
        s.dataset.hint = opts.hint || ctx.hint;
        return s;
    }

    /** ช่องติ๊ก */
    function cb(group, mode, extra) {
        const c = el('span', 'cb', OFF);
        c.setAttribute('role', mode === 'radio' ? 'radio' : 'checkbox');
        c.setAttribute('aria-checked', 'false');
        c.tabIndex = 0;
        c.dataset.group = group;
        c.dataset.mode = mode;
        if (extra) Object.assign(c.dataset, extra);
        return c;
    }

    function headingText(number, title) {
        const n = String(number || '');
        const num = /^(\d+|[A-Z])$/.test(n) ? n + '.' : n;   // "3" -> "3." / "A" -> "A." / "3.1" คงเดิม
        return (num ? num + ' ' : '') + title;
    }

    const hintNode = text => blk(el('div', 'hint guide', text));

    // ---------------------------------------------------------------- header / footer (ใช้ซ้ำในขั้นที่ 2)
    function buildHeader(data, ctx) {
        const h = el('div', 'hdr');
        const left = el('div', 'hdr-l');
        left.appendChild(document.createTextNode('Version '));
        left.appendChild(ph('form_version', ctx, { hint: '......' }));
        left.appendChild(document.createTextNode(' Date '));
        left.appendChild(ph('form_date', ctx, { hint: '..............' }));
        h.appendChild(left);
        h.appendChild(el('div', 'hdr-r', data.form_code || 'AP 02/2026'));
        return h;
    }

    function buildFooterText(data, lang, page, total) {
        const f = data.footer || {};
        const tpl = pick(f, 'text', lang) || (lang === 'en' ? 'Page {PAGE} from {NUMPAGES}' : 'หน้า {PAGE} จาก {NUMPAGES}');
        return tpl.replace('{PAGE}', page).replace('{NUMPAGES}', total);
    }

    // ---------------------------------------------------------------- field builders
    function listItem(id, i, bullet, ctx) {
        const li = blk(el('div', 'li'));
        li.appendChild(el('span', 'no', bullet ? '-' : (i + 1) + '.'));
        li.appendChild(ph(id + '.' + i, ctx));
        return li;
    }

    function listBlock(f, ctx, parent, bullet) {
        const n = f.min_items || (bullet ? 2 : 1);
        const wrap = el('div', 'nlist');
        wrap.dataset.list = f.id;
        wrap.dataset.min = String(n);
        wrap.dataset.marker = bullet ? 'bullet' : 'number';
        for (let i = 0; i < n; i++) wrap.appendChild(listItem(f.id, i, bullet, ctx));
        parent.appendChild(wrap);
    }

    function optionsBlock(f, ctx, mode, parent) {
        const opts = pick(f, 'options', ctx.lang) || [];
        opts.forEach((text, i) => {
        const row = blk(el('div', 'opt'));
        row.appendChild(cb(f.id, mode === 'checklist' ? 'check' : mode));
        const tx = el('div', 'tx');
        tx.appendChild(document.createTextNode(text));
        const detail = mode !== 'checklist' &&
            (f.with_detail ? !NO_DETAIL_RX.test(text) : DETAIL_RX.test(text));
        if (detail) {
            tx.appendChild(document.createTextNode(' '));
            tx.appendChild(ph(f.id + '.' + i, ctx, { hint: ctx.detailHint }));
        }
        row.appendChild(tx);
        parent.appendChild(row);
        });
    }

    function tableBlock(f, ctx, parent) {
        const cols = pick(f, 'columns', ctx.lang) || [];
        const rows = pick(f, 'rows', ctx.lang);
        const isGantt = f.id === 'gantt';
        const redCols = f.red_columns || [];
        const t = blk(el('table', 'dt' + (isGantt ? ' gantt' : '')));
        t.dataset.table = f.id;

        if (isGantt && cols.length === 10) {
        const cg = el('colgroup');
        ['28%'].concat(Array(8).fill('7%'), ['16%']).forEach(w => {
            const c = el('col'); c.style.width = w; cg.appendChild(c);
        });
        t.appendChild(cg);
        }

        const thead = el('thead');
        const trh = el('tr');
        cols.forEach((c, i) => {
        const cls = [];
        if (isGantt && i > 0 && i < cols.length - 1) cls.push('ctr');
        if (redCols.indexOf(i) >= 0) cls.push('red');
        trh.appendChild(el('th', cls.join(' '), c));
        });
        thead.appendChild(trh);
        t.appendChild(thead);

        const tbody = el('tbody');
        const count = rows ? rows.length : (f.min_rows || 1);
        const firstIsNo = /^(ลำดับ|no\.?)$/i.test(String(cols[0] || '').trim());

        for (let r = 0; r < count; r++) {
        const tr = el('tr');

        if (Array.isArray(f.row_options)) {          // ตารางยา: ชื่อยา + ตัวเลือก
            const tdName = el('td');
            tdName.appendChild(ph(f.id + '.' + r + '.name', ctx));
            const tdOpt = el('td');
            (pick(f, 'row_options', ctx.lang) || []).forEach(text => {
            const row = el('div', 'opt');
            row.appendChild(cb(f.id + '.' + r, 'radio'));
            row.appendChild(el('div', 'tx', text));
            tdOpt.appendChild(row);
            });
            tr.appendChild(tdName);
            tr.appendChild(tdOpt);
            tbody.appendChild(tr);
            continue;
        }

        cols.forEach((c, ci) => {
            const td = el('td');
            const key = f.id + '.' + r + '.' + ci;
            if (ci === 0 && rows) {
            const txt = rows[r];
            if (/^\d+\)\s*$/.test(txt)) {              // แถวว่างท้ายตาราง เช่น "9)"
                td.appendChild(document.createTextNode(txt + ' '));
                td.appendChild(ph(key, ctx));
            } else {
                td.textContent = txt;
            }
            } else if (ci === 0 && firstIsNo) {
            td.className = 'ctr';
            td.textContent = String(r + 1);
            } else if (ci === 0 && f.id === 'outcomes') {
            td.appendChild(el('span', 'no', (r + 1) + ')'));
            td.appendChild(ph(key, ctx));
            } else if (/\(\/\)/.test(c)) {               // คอลัมน์ติ๊ก "(/)"
            td.className = 'ctr';
            td.appendChild(cb(f.id + '.' + r, 'check'));
            } else {
            td.className = 'cell';
            td.contentEditable = 'true';
            td.spellcheck = false;
            td.dataset.key = key;
            }
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
        }
        t.appendChild(tbody);
        parent.appendChild(t);
    }

    function renderFields(fields, ctx, parent, single) {
        let kv = null;
        fields.forEach(f => {
        const label = pick(f, 'label', ctx.lang);
        const hint = pick(f, 'hint', ctx.lang);

        // ช่องข้อความสั้นที่อยู่ติดกัน รวมเป็นตาราง "ป้ายชื่อ | ช่องกรอก"
        if (f.type === 'text' && !single) {
            if (!kv) {
            kv = blk(el('table', 'dt kv'));
            kv.appendChild(el('tbody'));
            parent.appendChild(kv);
            }
            const tr = el('tr');
            tr.appendChild(el('td', 'k', label));
            const v = el('td', 'v');
            if (hint) v.appendChild(el('div', 'hint guide', hint));
            v.appendChild(ph(f.id, ctx));
            tr.appendChild(v);
            kv.firstChild.appendChild(tr);
            return;
        }
        kv = null;

        // หัวข้อที่มีช่องเดียว: ป้ายชื่อคือข้อความแนะนำของฟอร์ม (guide)
        if (label && !(single && f.type === 'text')) {
            parent.appendChild(blk(el('div', single ? 'lbl guide' : 'lbl', label)));
        }
        if (hint && f.type !== 'table') parent.appendChild(hintNode(hint));

        switch (f.type) {
            case 'text':       parent.appendChild(blk(ph(f.id, ctx, { multiline: true }))); break;
            case 'textarea':   parent.appendChild(blk(ph(f.id, ctx, { multiline: true }))); break;
            case 'numbered_list': listBlock(f, ctx, parent, false); break;
            case 'bullet_list':   listBlock(f, ctx, parent, true); break;
            case 'checkbox_group': optionsBlock(f, ctx, 'check', parent); break;
            case 'radio':      optionsBlock(f, ctx, 'radio', parent); break;
            case 'checklist':  optionsBlock(f, ctx, 'checklist', parent); break;
            case 'table':
            tableBlock(f, ctx, parent);
            if (hint) parent.appendChild(hintNode(hint));
            break;
            default:
            console.warn('ap02_renderer: ไม่รองรับชนิดช่อง', f.type, f.id);
            parent.appendChild(el('div', 'lbl', '[ไม่รองรับชนิดช่อง: ' + f.type + ']'));
        }
        });
    }

    function renderSection(sec, ctx, parent, depth) {
        const wrap = el('div', 'sec d' + depth);
        wrap.dataset.sec = sec.id;
        parent.appendChild(wrap);

        const title = headingText(sec.number, pick(sec, 'title', ctx.lang));
        let body = wrap;

        if (sec.gate) {                                   // 12.2 A-G: ใช่ / ไม่ใช่
        const g = sec.gate;
        const gw = el('div', 'gate-wrap');
        const t = blk(el('table', 'dt gate'));
        const tr = el('tr');
        tr.appendChild(el('td', 'k h', title));
        const o = el('td', 'gopts');
        [['no', pick(g, 'no_label', ctx.lang)], ['yes', pick(g, 'yes_label', ctx.lang)]].forEach(pair => {
            const row = el('div', 'opt');
            row.appendChild(cb(g.id, 'radio', { gate: pair[0] }));
            row.appendChild(el('div', 'tx', pair[1]));
            o.appendChild(row);
        });
        tr.appendChild(o);
        t.appendChild(tr);
        gw.appendChild(t);
        body = el('div', 'gate-body');
        gw.appendChild(body);
        wrap.appendChild(gw);
        } else {
        wrap.appendChild(blk(el('div', 'h l' + Math.min(depth, 2), title)));
        }

        const hint = pick(sec, 'hint', ctx.lang);
        if (hint) body.appendChild(hintNode(hint));

        if (sec.fields) {
        const single = depth === 0 && sec.fields.length === 1 && !sec.subsections;
        renderFields(sec.fields, ctx, body, single);
        }
        if (sec.subsections) {
        sec.subsections.forEach(s => renderSection(s, ctx, body, depth + 1));
        }
    }

    // ---------------------------------------------------------------- interaction (พื้นฐาน)
    function setCb(c, on) {
        c.setAttribute('aria-checked', on ? 'true' : 'false');
        c.textContent = on ? ON : OFF;
    }

    function toggleCb(doc, c) {
        const on = c.getAttribute('aria-checked') === 'true';
        if (c.dataset.mode === 'radio' && !on) {
        doc.querySelectorAll('.cb').forEach(o => {
            if (o !== c && o.dataset.group === c.dataset.group) setCb(o, false);
        });
        }
        setCb(c, !on);
        const gw = c.closest('.gate-wrap');
        if (gw && c.dataset.gate) {
        const no = gw.querySelector('.cb[data-gate="no"]');
        gw.querySelector('.gate-body').hidden = no.getAttribute('aria-checked') === 'true';
        }
    }

    function bind(doc) {
        doc.addEventListener('click', e => {
        const c = e.target.closest('.cb');
        if (c) toggleCb(doc, c);
        });
        doc.addEventListener('keydown', e => {
        const c = e.target.closest && e.target.closest('.cb');
        if (c && (e.key === ' ' || e.key === 'Enter')) { e.preventDefault(); toggleCb(doc, c); return; }
        const p = e.target.closest && e.target.closest('.ph');
        if (p && e.key === 'Enter' && !p.classList.contains('ml')) e.preventDefault();
        });
        doc.addEventListener('input', e => {
        const p = e.target.closest && e.target.closest('.ph');
        if (p) p.classList.toggle('filled', p.textContent.trim() !== '');
        });
        doc.addEventListener('paste', e => {
        const f = e.target.closest && e.target.closest('.ph, td.cell');
        if (!f) return;
        e.preventDefault();
        let t = (e.clipboardData || global.clipboardData).getData('text/plain') || '';
        if (!(f.classList.contains('ml') || f.tagName === 'TD')) t = t.replace(/\s*\n\s*/g, ' ');
        document.execCommand('insertText', false, t);
        });
    }

    // ---------------------------------------------------------------- public API
    let cachedData = null;
    let cachedUrl = null;

    function load(url) {
        const u = url || DEFAULT_URL;
        if (cachedData && cachedUrl === u) return Promise.resolve(cachedData);
        return fetch(u, { cache: 'no-cache' }).then(res => {
        if (!res.ok) {
            throw new Error('โหลด ' + u + ' ไม่ได้ (HTTP ' + res.status +
            ') ตรวจว่าคัดลอกไฟล์ JSON ไปไว้ที่ frontend/templates/ap02.json แล้ว');
        }
        return res.json();
        }).then(data => {
        if (!data || !Array.isArray(data.sections)) throw new Error('ไฟล์ ' + u + ' ไม่มีรายการ sections');
        cachedData = data;
        cachedUrl = u;
        return data;
        });
    }

    function render(host, data, opts) {
        opts = opts || {};
        const lang = opts.lang === 'en' ? 'en' : 'th';
        const ctx = {
        lang: lang,
        hint: lang === 'en' ? 'Enter text…' : 'กรอกข้อมูล…',
        detailHint: lang === 'en' ? 'Specify…' : 'ระบุ…',
        };
        injectStyle();
        host.innerHTML = '';

        const doc = el('div', 'ap02-doc' + (opts.showHints === false ? ' no-hints' : ''));
        doc.lang = lang;
        const flow = el('div', 'ap02-flow');

        flow.appendChild(buildHeader(data, ctx));
        flow.appendChild(blk(el('div', 'doc-title', lang === 'en' ? data.title_en_form : data.title_th_form)));
        data.sections.forEach(s => renderSection(s, ctx, flow, 0));

        doc.appendChild(flow);
        host.appendChild(doc);
        bind(doc);
        return { doc: doc, flow: flow, ctx: ctx };
    }

    function show(host, lang, opts) {
        return load().then(data => render(host, data, Object.assign({ lang: lang }, opts || {})));
    }

    global.Ap02Renderer = {
        load: load, render: render, show: show,
        buildHeader: buildHeader, buildFooterText: buildFooterText,
    };
    })(window);