/*
 * suspects.js - แสดง "รายการจุดสงสัย" ที่ backend (suspects.py) พบในไฟล์ต้นฉบับ
 *
 * ใช้งาน: window.EthicSuspects.render(suspects, blocks)  /  window.EthicSuspects.clear()
 *   suspects = result.suspects จาก /api/documents/analyze
 *   blocks   = result.blocks   (ใช้ดึงข้อความรอบจุดสงสัยมาแสดงเป็นบริบท)
 *
 * หมายเหตุ:
 *  - ตำแหน่ง start/end อ้างอิงข้อความในก้อนต้นฉบับ ไม่ใช่เอกสารที่ระบบสร้างขึ้น
 *  - ข้อความทุกชิ้นมาจากไฟล์ของผู้ใช้ จึงใส่ด้วย textContent / createTextNode เท่านั้น ห้ามใช้ innerHTML
 */
(function (root) {
    'use strict';

  var LIMIT = 200;      // แสดงสูงสุดกี่รายการ (กันหน้าเว็บหนักเมื่อไฟล์มีจุดสงสัยจำนวนมาก)
  var CONTEXT = 30;     // แสดงข้อความรอบจุดสงสัยข้างละกี่ตัวอักษร
    var LABEL = { red: 'ควรแก้', yellow: 'ควรตรวจ' };

    function $(id) { return document.getElementById(id); }

    function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) { e.className = cls; }
    if (text !== undefined && text !== null) { e.textContent = text; }
    return e;
    }

    function clear() {
    $('suspectPanel').hidden = true;
    $('suspectList').textContent = '';
    $('suspectList').removeAttribute('data-only-red');
    $('suspectOnlyRed').checked = false;
    $('suspectFilter').hidden = true;
    }

  // ตำแหน่งที่ผู้ใช้เปิดไฟล์ต้นฉบับแล้วหาเจอ: PDF มีเลขหน้า / DOCX ไม่มีหน้า จึงใช้ลำดับส่วนที่ระบบอ่านได้แทน
  // (ลำดับนี้นับย่อหน้าและเซลล์ตาราง อาจไม่ตรงกับที่เห็นใน Word ให้ใช้ข้อความรอบจุดเป็นตัวหาหลัก)
    function where(sp) {
    if (sp.page !== null && sp.page !== undefined) { return 'หน้า ' + sp.page; }
    return 'ส่วนที่ ' + (Number(sp.block_index) + 1);
    }

  // ข้อความรอบจุดสงสัย พร้อมไฮไลต์ตัวที่สงสัย
    function snippet(sp, blockText) {
    var box = el('div', 'suspect-snippet');
    var full = typeof blockText === 'string' ? blockText : null;
    var start = Number(sp.start), end = Number(sp.end);

    if (full === null || !(start >= 0) || !(end >= start) || end > full.length) {
      box.appendChild(el('mark', null, String(sp.text || '')));   // ไม่มีบริบท ใช้ข้อความที่ backend ส่งมา
        return box;
    }
    var from = Math.max(0, start - CONTEXT);
    var to = Math.min(full.length, end + CONTEXT);
    var flat = function (t) { return t.replace(/\s+/g, ' '); };

    var marked = full.slice(start, end);
    if (!marked.trim()) { marked = '\u2423'; }                    // ช่องว่างล้วน แสดงเป็นสัญลักษณ์ให้มองเห็น

    box.appendChild(document.createTextNode((from > 0 ? '\u2026' : '') + flat(full.slice(from, start))));
    box.appendChild(el('mark', null, marked));
    box.appendChild(document.createTextNode(flat(full.slice(end, to)) + (to < full.length ? '\u2026' : '')));
    return box;
    }

    function render(suspects, blocks) {
    clear();
    if (!Array.isArray(suspects)) { return; }

    var byIndex = {};
    (blocks || []).forEach(function (b) { byIndex[b.index] = b.text; });

    var reds = 0, yellows = 0;
    suspects.forEach(function (sp) { if (sp.severity === 'red') { reds++; } else { yellows++; } });

    $('suspectSummary').textContent = suspects.length
        ? 'พบ ' + suspects.length + ' จุด: ควรแก้ ' + reds + ' / ควรตรวจ ' + yellows
        : 'ไม่พบจุดสงสัยตามกฎที่ระบบใช้ตรวจ (ไม่ได้แปลว่าไฟล์ไม่มีข้อผิดพลาดเลย)';

    var ordered = suspects.slice().sort(function (a, b) {
        var ra = a.severity === 'red' ? 0 : 1, rb = b.severity === 'red' ? 0 : 1;
        return ra - rb || (a.block_index - b.block_index) || (a.start - b.start);
    });

    var list = $('suspectList');
    ordered.slice(0, LIMIT).forEach(function (sp) {
        var sev = sp.severity === 'red' ? 'red' : 'yellow';
        var li = el('li', 'suspect-item suspect--' + sev);
        li.appendChild(el('span', 'suspect-badge', LABEL[sev]));
        li.appendChild(el('div', 'suspect-where', where(sp)));
        li.appendChild(el('div', 'suspect-reason', String(sp.reason || '')));
        li.appendChild(snippet(sp, byIndex[sp.block_index]));
        if (sp.suggestion) { li.appendChild(el('div', 'suspect-fix', 'ข้อเสนอ: ' + sp.suggestion)); }
        list.appendChild(li);
    });

    if (ordered.length > LIMIT) {
        list.appendChild(el('li', 'suspect-more',
        'แสดง ' + LIMIT + ' จาก ' + ordered.length + ' จุด (เรียงรายการสีแดงก่อน)'));
    }
    $('suspectFilter').hidden = !(reds && yellows);
    $('suspectPanel').hidden = false;
    }

  // ตัวกรอง "เฉพาะสีแดง"
    function init() {
    var box = $('suspectOnlyRed');
    if (!box) { return; }
    box.addEventListener('change', function () {
        var list = $('suspectList');
        if (box.checked) { list.setAttribute('data-only-red', 'true'); } else { list.removeAttribute('data-only-red'); }
    });
    }

  // เปลี่ยน/ลบไฟล์ -> ผลตรวจของไฟล์เก่าต้องหายไป (ไม่ให้ผู้ใช้เข้าใจผิดว่าเป็นของไฟล์ใหม่)
    document.addEventListener('ethic:file', function (e) {
    var st = e.detail && e.detail.status;
    if (st === 'checking' || st === 'rejected' || st === 'cleared') { clear(); }
    });

    if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', init); } else { init(); }

    root.EthicSuspects = { render: render, clear: clear };
})(typeof window !== 'undefined' ? window : globalThis);