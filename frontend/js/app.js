(function () {
  'use strict';

  // ----------------------------------------------------------------
  // ตั้งค่า
  // ----------------------------------------------------------------
  // หา path ของ templates โดยอัตโนมัติตาม URL ปัจจุบัน
  // ตัวอย่าง: /frontend/index.html → /templates/ap02.json
  //           /Ethic-MFU/frontend/index.html → /Ethic-MFU/templates/ap02.json
  var _m = location.pathname.match(/^(.*?)\/frontend\//);
  var TEMPLATE_URL = (_m ? _m[1] : '') + '/templates/ap02.json';
  var template = null;
  var lang = 'th';
  var activeVariant = 0;
  var g_document_blocks = null;  // เก็บบล็อก
  var g_filled_form = null;      // เก็บผลลัพธ์ API

  // ----------------------------------------------------------------
  // ข้อความที่ระบบสร้างเอง แยกตามภาษา
  // ----------------------------------------------------------------
  var S = {
    th: {
      fill: function (l) { return '[กรอก: ' + l + ']'; },
      notFound: '[ไม่พบข้อมูลในไฟล์ กรุณาตรวจสอบหรือกรอกเอง]',
      blank: '[ ........ ]',
      notSelected: '[ยังไม่ได้เลือก]',
      gateUnknown: '[ระบุว่าใช่หรือไม่ใช่]',
      page: function (n, t) { return 'หน้า ' + n + ' จาก ' + t; },
      summaryTitle: 'สรุปโครงการโดยย่อ',
      sumTitle: 'ชื่อโครงการ', sumPI: 'ผู้วิจัยหลัก', sumPeriod: 'ช่วงเวลาวิจัย',
      sumDesign: 'รูปแบบการวิจัย', sumObj: 'วัตถุประสงค์หลัก', sumSample: 'ขนาดตัวอย่าง'
    },
    en: {
      fill: function (l) { return '[Fill in: ' + l + ']'; },
      notFound: '[Not found in the file - please check or complete]',
      blank: '[ ........ ]',
      notSelected: '[Not selected]',
      gateUnknown: '[Specify Yes or No]',
      page: function (n, t) { return 'Page ' + n + ' from ' + t; },
      summaryTitle: 'Project Summary',
      sumTitle: 'Title', sumPI: 'Principal Investigator', sumPeriod: 'Study period',
      sumDesign: 'Study design', sumObj: 'Primary objective', sumSample: 'Sample size'
    }
  };

  // ----------------------------------------------------------------
  // ข้อมูลที่สกัดได้จากไฟล์ของผู้ใช้ (เริ่มว่างทุกครั้งที่กดสร้างเอกสาร)
  // หลักการ: ช่องไหนหาในไฟล์ไม่เจอ ต้องแสดงเป็นช่องสีแดงให้ผู้ใช้กรอกเอง
  // ห้ามเติมข้อความตัวอย่างหรือเดาค่าให้ (รวมถึงเกต A-G ที่ตอบ ใช่/ไม่ใช่)
  // ----------------------------------------------------------------
  var DATA = {};

  // ----------------------------------------------------------------
  // 4 แบบที่แตกต่างกัน
  // ----------------------------------------------------------------
  var VARIANTS = [
    { name: 'แบบที่ 1 ฟอร์มมาตรฐาน',
      desc: 'เรียงตามฟอร์ม AP 02/2026 ครบทุกหัวข้อ ชื่อหัวข้อแยกบรรทัดเหนือเนื้อหา แสดงคำอธิบายในฟอร์ม และแสดงส่วนเรื่องเฉพาะ A-G ทั้งหมด',
      opts: { labels: 'block', optional: 'show', hideInstructions: false, summary: false, cls: 'sp-normal' } },
    { name: 'แบบที่ 2 ฉบับกระชับ',
      desc: 'ตัดส่วนเรื่องเฉพาะ A-G ที่ไม่เกี่ยวข้อง ตัดคำอธิบายในฟอร์ม ชื่อหัวข้อและเนื้อหาอยู่บรรทัดเดียวกัน เว้นระยะแน่น ใช้จำนวนหน้าน้อยที่สุด',
      opts: { labels: 'inline', optional: 'omit', hideInstructions: true, summary: false, cls: 'sp-tight' } },
    { name: 'แบบที่ 3 ตารางกรอบ',
      desc: 'ทุกหัวข้อเป็นกรอบสองคอลัมน์ (ชื่อหัวข้อ | เนื้อหา) ให้ความรู้สึกเหมือนฟอร์มกระดาษ',
      opts: { labels: 'table', optional: 'show', hideInstructions: false, summary: false, cls: 'sp-normal' } },
    { name: 'แบบที่ 4 สรุปก่อน',
      desc: 'เริ่มด้วยกรอบสรุปโครงการ ตามด้วยเนื้อหาครบ เว้นระยะกว้างอ่านง่าย ตัดส่วนเรื่องเฉพาะที่ไม่เกี่ยวข้อง',
      opts: { labels: 'block', optional: 'omit', hideInstructions: true, summary: true, cls: 'sp-airy' } }
  ];

  // ----------------------------------------------------------------
  // ตัวช่วยทั่วไป & การเชื่อมต่อ Backend
  // ----------------------------------------------------------------
  function $(id) { return document.getElementById(id); }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) { e.className = cls; }
    if (text !== undefined && text !== null) { e.textContent = text; }
    return e;
  }

  function tx(o, k) {
    if (lang === 'en') {
      var v = o[k + '_en'];
      if (v !== undefined && v !== null) { return v; }
    }
    return (o[k] === undefined || o[k] === null) ? '' : o[k];
  }

  function arr(o, k) {
    if (lang === 'en' && o[k + '_en']) { return o[k + '_en']; }
    return o[k] || [];
  }

  function dv(id) { return DATA[id]; }

  var DRAFT = {};          // { id ช่อง: [เลข block ที่ AI อ้างอิง] } ช่องที่ AI ร่างให้ (สีเหลือง ต้องตรวจทาน)
  var userEdited = false;   // ผู้ใช้แก้เอกสารในหน้าตัวอย่างแล้วหรือยัง (ใช้เตือนก่อนสร้างใหม่)
  // เก็บข้อความเดิมของช่องสีแดงไว้ใน data-orig เพื่อเทียบว่าผู้ใช้แก้แล้วหรือยัง
  function ph(text) { var s = el('span', 'ph', text); s.dataset.orig = text; return s; }

  function blockPh(text) {
    var d = el('div', 'para');
    d.appendChild(ph(text));
    return d;
  }

  // ป้ายบอกที่มาของร่าง AI: "หน้า 12, 14" (PDF) หรือ "ส่วนที่ 5" (DOCX ไม่มีเลขหน้า)
  function srcLabel(ids) {
    var blocks = (window.lastResult && window.lastResult.blocks) || [];
    var byIdx = {};
    blocks.forEach(function (b) { byIdx[b.index] = b; });
    var pages = [], parts = [];
    (ids || []).forEach(function (i) {
      var b = byIdx[i];
      if (b && b.page != null) { if (pages.indexOf(b.page) < 0) { pages.push(b.page); } }
      else { parts.push(i + 1); }
    });
    pages.sort(function (x, y) { return x - y; });
    var out = [];
    if (pages.length) { out.push('หน้า ' + pages.slice(0, 8).join(', ') + (pages.length > 8 ? ' ...' : '')); }
    if (parts.length) { out.push('ส่วนที่ ' + parts.slice(0, 8).join(', ')); }
    return out.join(' / ');
  }

  // ใส่ข้อความที่พบจากไฟล์ ถ้าเป็นร่างจาก AI ให้ครอบด้วย span.ai (สีเหลือง) พร้อมคำอธิบาย
  function valueInto(parent, str, fid) {
    if (!DRAFT[fid]) { return richInto(parent, str); }
    var s = el('span', 'ai');
    s.title = 'ร่างจาก AI (ต้องตรวจทาน) อ้างอิง' + srcLabel(DRAFT[fid]);
    richInto(s, str);
    parent.appendChild(s);
    return parent;
  }

  function richInto(parent, str) {
    var re = /\[\[(.+?)\|(.+?)\]\]/g, last = 0, m;
    while ((m = re.exec(str)) !== null) {
      if (m.index > last) { parent.appendChild(document.createTextNode(str.slice(last, m.index))); }
      var s = el('span', 'flag', m[1]);
      s.title = m[2];
      parent.appendChild(s);
      last = re.lastIndex;
    }
    if (last < str.length) { parent.appendChild(document.createTextNode(str.slice(last))); }
    return parent;
  }

  function numLabel(sec) {
    var n = sec.number || '';
    if (!n) { return ''; }
    if (/\.$/.test(n)) { return n; }
    if (/^\d+$/.test(n) || /^[A-G]$/.test(n)) { return n + '.'; }
    return n;
  }

  // ----------------------------------------------------------------
  // สร้างเนื้อหาของแต่ละช่อง
  // ----------------------------------------------------------------
  function optionRow(text, on) {
    var d = el('div', 'opt');
    d.appendChild(el('span', 'cb' + (on ? ' on' : '')));
    var t = el('span', 'tx');
    richInto(t, text);
    d.appendChild(t);
    return d;
  }

  function optsOf(f) { return arr(f, 'options'); }

  function renderTable(f) {
    var cols = arr(f, 'columns');
    var rows = arr(f, 'rows');
    var rowOpts = lang === 'en' ? f.row_options_en : f.row_options;
    var red = f.red_columns || [];
    var tbl = el('table', 'dt' + (f.id === 'gantt' ? ' gantt' : ''));
    var thead = el('thead');
    var trh = el('tr');
    cols.forEach(function (c, i) {
      trh.appendChild(el('th', red.indexOf(i) >= 0 ? 'redcol' : '', c));
    });
    thead.appendChild(trh);
    tbl.appendChild(thead);
    var tbody = el('tbody');
    var n = rows.length ? rows.length : (f.min_rows || 1);
    var indexCol = /^(ลำดับ|No\.)$/.test(cols[0] || '');
    for (var r = 0; r < n; r++) {
      var tr = el('tr');
      for (var ci = 0; ci < cols.length; ci++) {
        var td = el('td');
        if (rows.length && ci === 0) {
          td.textContent = rows[r];
        } else if (!rows.length && ci === 0 && indexCol) {
          td.textContent = String(r + 1);
        } else if (rowOpts && ci === 1) {
          rowOpts.forEach(function (o) { td.appendChild(optionRow(o, false)); });
        } else {
          td.className = 'blank';
        }
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    }
    tbl.appendChild(tbody);
    return tbl;
  }

  function renderValue(f) {
    var nodes = [], t = f.type, label = tx(f, 'label'), data = dv(f.id);

    if (t === 'text' || t === 'textarea') {
      var p = el('div', 'para');
      if (f.fill_by === 'user') { p.appendChild(ph(S[lang].fill(label))); }
      else if (typeof data === 'string' && data) { valueInto(p, data, f.id); }
      else { p.appendChild(ph(S[lang].notFound)); }
      nodes.push(p);

    } else if (t === 'numbered_list' || t === 'bullet_list') {
      var items = Array.isArray(data) ? data : [];
      var n = Math.max(items.length, f.min_items || 2);
      for (var i = 0; i < n; i++) {
        var row = el('div', 'item');
        row.appendChild(el('span', 'mk', t === 'numbered_list' ? (i + 1) + '.' : '-'));
        var c = el('span', 'tx');
        if (items[i]) { valueInto(c, items[i], f.id); }
        else { c.appendChild(ph(items.length === 0 && i === 0 ? S[lang].notFound : S[lang].blank)); }
        row.appendChild(c);
        nodes.push(row);
      }

    } else if (t === 'checkbox_group' || t === 'radio' || t === 'checklist') {
      var sel = Array.isArray(data) ? data : [];
      optsOf(f).forEach(function (o, idx) { nodes.push(optionRow(o, sel.indexOf(idx) >= 0)); });
      if (t !== 'checklist' && f.fill_by !== 'user' && sel.length === 0) { nodes.push(blockPh(S[lang].notSelected)); }

    } else if (t === 'table') {
      nodes.push(renderTable(f));

    } else {
      nodes.push(blockPh(S[lang].notFound));
    }
    return nodes;
  }

  // ----------------------------------------------------------------
  // วางช่อง/หัวข้อเป็น บล็อก
  // ----------------------------------------------------------------
  function pushField(f, opts, blocks, skipLabel) {
    var label = tx(f, 'label');
    var hint = tx(f, 'hint');
    var longLabel = label.length > 70;
    var nodes = renderValue(f);

    if (opts.labels === 'table') {
      nodes.forEach(function (n, i) {
        var row = el('div', 'boxrow' + (longLabel ? ' full' : '') + (i ? ' cont' : ''));
        if (!(longLabel && i > 0)) {
          var l = el('div', 'lbl');
          if (i === 0) {
            l.textContent = label;
            if (hint && !opts.hideInstructions) { l.appendChild(el('div', 'hint', hint)); }
          }
          row.appendChild(l);
        }
        var v = el('div', 'val');
        v.appendChild(n);
        row.appendChild(v);
        blocks.push(row);
      });
      return;
    }

    if (!skipLabel) {
      if (opts.labels === 'inline' && nodes.length === 1 && nodes[0].classList.contains('para') && !longLabel) {
        var p = el('div', 'para');
        p.appendChild(el('strong', null, label + ': '));
        while (nodes[0].firstChild) { p.appendChild(nodes[0].firstChild); }
        blocks.push(p);
        return;
      }
      var lb = el('div', 'lbl-line' + (longLabel ? ' instr' : ''), label);
      lb.dataset.keep = '1';
      blocks.push(lb);
      if (hint && !opts.hideInstructions) {
        var hEl = el('div', 'hint', hint);
        hEl.dataset.keep = '1';
        blocks.push(hEl);
      }
    }
    nodes.forEach(function (n) { blocks.push(n); });
  }

  function pushSection(sec, depth, opts, blocks) {
    var gate = sec.gate;
    var gv = gate ? dv(gate.id) : undefined;   // true / false / undefined (ยังไม่ทราบ)
    if (gate && opts.optional === 'omit' && gv === false) { return; }
    // ยังไม่ทราบว่าใช่หรือไม่: แบบที่ตัดส่วนเฉพาะ จะแสดงแค่หัวข้อกับตัวเลือก ให้ผู้ใช้ตอบก่อน
    var gateUnknownCompact = gate && opts.optional === 'omit' && gv === undefined;

    var local = [];
    var sh = tx(sec, 'hint');
    if (sh && !opts.hideInstructions) {
      var shEl = el('div', 'hint', sh);
      shEl.dataset.keep = '1';
      local.push(shEl);
    }

    if (gate) {
      local.push(optionRow(tx(gate, 'no_label'), gv === false));
      local.push(optionRow(tx(gate, 'yes_label'), gv === true));
      if (gv === undefined) { local.push(blockPh(S[lang].gateUnknown)); }
    }
    if (!(gate && gv === false) && !gateUnknownCompact) {
      var fields = sec.fields || [];
      fields.forEach(function (f) {
        var skip = opts.hideInstructions && fields.length === 1 && (f.type === 'text' || f.type === 'textarea');
        pushField(f, opts, local, skip);
      });
      (sec.subsections || []).forEach(function (s) { pushSection(s, depth + 1, opts, local); });
    }

    if (!(sec.fields || []).length && (sec.subsections || []).length && local.length === 0) { return; }

    var h = el('div', depth === 0 ? 'sec-h' : 'sub-h', (numLabel(sec) + ' ' + tx(sec, 'title')).trim());
    h.dataset.keep = '1';
    blocks.push(h);
    local.forEach(function (b) { blocks.push(b); });
  }

  function summaryBlock() {
    var box = el('div', 'summary');
    box.appendChild(el('div', 'sum-h', S[lang].summaryTitle));
    function row(label, valueNode) {
      var r = el('div', 'sum-row');
      r.appendChild(el('b', null, label));
      var v = el('span');
      v.appendChild(valueNode);
      r.appendChild(v);
      box.appendChild(r);
    }
    function textOrPh(v) {
      var s = el('span');
      if (typeof v === 'string' && v) { richInto(s, v); } else { s.appendChild(ph(S[lang].notFound)); }
      return s;
    }
    var obj = dv('objective_primary');
    row(S[lang].sumTitle, textOrPh(dv(lang === 'en' ? 'title_en' : 'title_th')));
    row(S[lang].sumPI, ph(S[lang].fill(S[lang].sumPI)));
    row(S[lang].sumPeriod, ph(S[lang].fill(S[lang].sumPeriod)));
    row(S[lang].sumDesign, textOrPh(dv('study_design')));
    row(S[lang].sumObj, textOrPh(Array.isArray(obj) ? obj[0] : ''));
    row(S[lang].sumSample, textOrPh(dv('sample_size')));
    return box;
  }

  function buildBlocks(opts) {
    var blocks = [];
    var t = el('div', 'doc-title', lang === 'en' ? template.title_en_form : template.title_th_form);
    t.dataset.keep = '1';
    blocks.push(t);
    if (opts.summary) { blocks.push(summaryBlock()); }
    template.sections.forEach(function (s) { pushSection(s, 0, opts, blocks); });
    return blocks;
  }

  // ----------------------------------------------------------------
  // แบ่งหน้า A4 + header/footer
  // ----------------------------------------------------------------
  function newPage(container, cls) {
    var sheet = el('div', 'sheet ' + cls);
    var hdr = el('div', 'hdr');
    var left = el('span');
    left.appendChild(document.createTextNode('Version'));
    left.appendChild(ph('......'));
    left.appendChild(document.createTextNode(' Date'));
    left.appendChild(ph('...................'));
    hdr.appendChild(left);
    hdr.appendChild(el('span', null, template.form_code || 'AP 02/2026'));
    var body = el('div', 'body');
    var ftr = el('div', 'ftr');
    ftr.appendChild(el('span', 'pgno'));
    sheet.appendChild(hdr);
    sheet.appendChild(body);
    sheet.appendChild(ftr);
    container.appendChild(sheet);
    return { sheet: sheet, body: body };
  }

  function overflows(body) { return body.scrollHeight > body.clientHeight + 1; }

  function paginate(blocks, container, cls) {
    container.textContent = '';
    var page = newPage(container, cls);
    var oversize = 0;
    blocks.forEach(function (b) {
      page.body.appendChild(b);
      if (overflows(page.body)) {
        if (page.body.children.length > 1) {
          page.body.removeChild(b);
          var moved = [];
          while (page.body.children.length > 1 && page.body.lastElementChild.dataset.keep === '1') {
            moved.unshift(page.body.removeChild(page.body.lastElementChild));
          }
          page = newPage(container, cls);
          moved.forEach(function (m) { page.body.appendChild(m); });
          page.body.appendChild(b);
          if (overflows(page.body) && page.body.children.length === 1) { oversize++; }
        } else {
          oversize++;
        }
      }
    });
    var sheets = container.querySelectorAll('.sheet');
    for (var i = 0; i < sheets.length; i++) {
      sheets[i].querySelector('.pgno').textContent = S[lang].page(i + 1, sheets.length);
    }
    return { pages: sheets.length, oversize: oversize };
  }

  // ----------------------------------------------------------------
  // การแก้ไขเนื้อหาและตรวจสอบฟอนต์
  // ----------------------------------------------------------------
  function enableEditing(container) {
    Array.prototype.forEach.call(container.querySelectorAll('.sheet'), function (sheet) {
      var body = sheet.querySelector('.body');
      body.setAttribute('contenteditable', 'true');
      body.setAttribute('spellcheck', 'false');
      Array.prototype.forEach.call(sheet.querySelectorAll('.hdr .ph'), function (h) {
        h.setAttribute('contenteditable', 'true');
      });
      Array.prototype.forEach.call(sheet.querySelectorAll('.cb'), function (c) {
        c.setAttribute('contenteditable', 'false');
      });
    });

    var current = null;

    function finish(t) {
      var txt = t.textContent.trim();
      if (!txt) {
        if (t.dataset.orig !== undefined) { t.textContent = t.dataset.orig; }
        t.classList.remove('filled');
      } else if (t.dataset.orig !== undefined && txt !== t.dataset.orig) {
        t.classList.add('filled');
      }
    }

    container.addEventListener('click', function (e) {
      var t = e.target.closest ? e.target.closest('.ph') : null;
      if (!t || t.classList.contains('filled')) { return; }
      if (t.dataset.orig === undefined) { t.dataset.orig = t.textContent; }
      current = t;
      var r = document.createRange();
      r.selectNodeContents(t);
      var sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(r);
    });

    container.addEventListener('beforeinput', function (e) {
      if (!current || e.inputType.indexOf('delete') !== 0) { return; }
      var sel = window.getSelection();
      if (sel.toString() === current.textContent && current.textContent.length) {
        e.preventDefault();
        current.textContent = current.dataset.orig;
        current.classList.remove('filled');
        var r = document.createRange();
        r.selectNodeContents(current);
        sel.removeAllRanges();
        sel.addRange(r);
      }
    });

    document.addEventListener('selectionchange', function () {
      if (!current) { return; }
      var sel = window.getSelection();
      var inside = sel.anchorNode && current.contains(sel.anchorNode);
      if (!inside) { finish(current); current = null; }
    });

    container.addEventListener('paste', function (e) {
      e.preventDefault();
      var text = (e.clipboardData || window.clipboardData).getData('text/plain');
      document.execCommand('insertText', false, text);
    });

    container.addEventListener('input', function (e) {
      var sheet = e.target.closest ? e.target.closest('.sheet') : null;
      if (!sheet) { return; }
      // ผู้ใช้พิมพ์ในช่องสีแดง: เปลี่ยนเป็นสีดำทันที (ไม่ต้องรอคลิกออกจากช่อง)
      userEdited = true;
      var sel = window.getSelection();
      var node = sel && sel.anchorNode ? (sel.anchorNode.nodeType === 1 ? sel.anchorNode : sel.anchorNode.parentElement) : null;
      var drafted = node && node.closest ? node.closest('.ai') : null;
      if (drafted) { drafted.classList.remove('ai'); drafted.removeAttribute('title'); }   // ผู้ใช้แก้แล้ว ถือว่าตรวจทานแล้ว
      var edited = node && node.closest ? node.closest('.ph') : null;
      if (edited) {
        var now = edited.textContent.trim();
        if (now && now !== edited.dataset.orig) { edited.classList.add('filled'); }
        else { edited.classList.remove('filled'); }
      }
      var td = e.target.closest ? e.target.closest('td.blank') : null;
      if (td && td.textContent.trim()) { td.classList.remove('blank'); }
      sheet.classList.toggle('over', overflows(sheet.querySelector('.body')));
      var n = document.querySelectorAll('.sheet.over').length;
      $('status').textContent = n
        ? 'คำเตือน: มี ' + n + ' หน้าที่เนื้อหาเกินกรอบ A4 หลังแก้ไข (ส่วนท้ายอาจถูกตัดตอนพิมพ์)'
        : 'แก้ไขเอกสารแล้ว (การแก้ไขของแต่ละแบบแยกจากกัน)';
    });
  }

  function hasThSarabun() {
    var c = document.createElement('canvas').getContext('2d');
    var t = 'ทดสอบภาษาไทย';
    c.font = '16px monospace';
    var a = c.measureText(t).width;
    c.font = "16px 'TH Sarabun New', monospace";
    return a !== c.measureText(t).width;
  }

  function showError(msg) {
    $('err-msg').textContent = msg;
    $('errorModal').hidden = false;
  }

  function loadTemplate() {
    if (location.protocol === 'file:') {
      return Promise.reject(new Error('ไม่สามารถเปิดไฟล์ตรงๆ ได้ กรุณาเปิดผ่าน Live Server (กด Go Live)'));
    }
    return fetch(TEMPLATE_URL, { cache: 'no-store' }).then(function (res) {
      if (!res.ok) {
        throw new Error('โหลด templates/ap02.json ไม่ได้ (รหัส ' + res.status + ')');
      }
      return res.json();
    }).then(function (data) {
      if (!data.sections || !data.sections.length) { throw new Error('โครงสร้างของ ap02.json ไม่ถูกต้อง'); }
      template = data;
    });
  }

  function nextFrame() { return new Promise(function (r) { requestAnimationFrame(function () { setTimeout(r, 0); }); }); }

  function selectedLang() {
    var r = document.querySelector('input[name="lang"]:checked');
    return r ? r.value : 'th';
  }

  function updatePickSummary() {
    var l = selectedLang();
    $('pick-summary').textContent = l === 'en'
      ? 'ภาษาที่เลือก: English \u2192 จะได้เอกสารภาษาอังกฤษ 4 แบบ'
      : 'ภาษาที่เลือก: ภาษาไทย \u2192 จะได้เอกสารภาษาไทย 4 แบบ';
  }

  function activate(idx) {
    activeVariant = idx;
    var tabs = $('tabs').children, vs = $('variants').children;
    for (var i = 0; i < tabs.length; i++) {
      tabs[i].setAttribute('aria-selected', i === idx ? 'true' : 'false');
      vs[i].classList.toggle('active', i === idx);
    }
    $('desc').textContent = VARIANTS[idx].desc;
  }

  // ----------------------------------------------------------------
  // กระบวนการสร้างเอกสารหลัก (Generate)
  // จัดหน้า A4 ทั้ง 4 แบบจาก DATA ปัจจุบัน (ใช้ทั้งตอนสร้างครั้งแรกและหลัง AI เติมช่อง)
  async function renderVariants(P, scroll) {
    userEdited = false;
    if (document.fonts && document.fonts.ready) { await document.fonts.ready; }

    // ขั้นตอนที่ 5: จัดหน้า A4 ทั้ง 4 แบบ
    if (P) { P.setStage('layout', 'active', 'กำลังจัดหน้าเอกสาร A4 ทั้ง 4 แบบ...'); }

    $('result').hidden = false;
    var host = $('variants');
    host.textContent = '';
    var tabs = $('tabs');
    tabs.textContent = '';
    var totalOversize = 0;

    for (var i = 0; i < VARIANTS.length; i++) {
      var v = VARIANTS[i];
      var c = el('div', 'variant measuring');
      host.appendChild(c);
      await nextFrame();

      var res = paginate(buildBlocks(v.opts), c, v.opts.cls);
      c.classList.remove('measuring');
      enableEditing(c);

      totalOversize += res.oversize;
      var tab = el('button', 'tab', v.name + ' (' + res.pages + ' หน้า)');
      tab.type = 'button';
      tab.setAttribute('role', 'tab');
      (function (idx) { tab.addEventListener('click', function () { activate(idx); }); })(i);
      tabs.appendChild(tab);
    }

    activate(0);

    if (P) { P.setStage('layout', 'done', 'จัดเอกสารครบ 4 แบบเรียบร้อย'); }

    applyZoom();
    var langName = lang === 'en' ? 'ภาษาอังกฤษ' : 'ภาษาไทย';
    $('status').textContent = 'สร้างเอกสาร' + langName + 'ครบ 4 แบบแล้ว เลือกดูได้จากแท็บด้านล่าง'
      + (totalOversize ? ' (พบ ' + totalOversize + ' ส่วนที่ยาวเกิน 1 หน้า)' : '');

    if (!hasThSarabun()) {
      $('status').textContent += ' | เครื่องนี้ไม่มีฟอนต์ TH Sarabun New จึงใช้ฟอนต์สำรอง';
    }

    if (scroll) { $('result').scrollIntoView({ behavior: 'smooth', block: 'start' }); }
  }

  // ----------------------------------------------------------------
  async function generate() {
    var btn = $('btn-generate');
    btn.disabled = true;
    $('status').textContent = 'กำลังสร้างเอกสาร...';
    if (window.EthicSuspects) { window.EthicSuspects.clear(); }   // ล้างผลของไฟล์ครั้งก่อนก่อนวิเคราะห์ใหม่
    
    var P = window.EthicProgress;
    var currentStage = '';   // จำว่ากำลังทำขั้นไหน เพื่อให้ catch ทำสีแดงถูกขั้น

    try {
      lang = selectedLang();
      document.documentElement.lang = lang;

      if (!template) { await loadTemplate(); }

      var file = window.EthicUpload && window.EthicUpload.getFile();
      if (!file) { throw new Error('กรุณาเลือกไฟล์ที่ผ่านการตรวจก่อนสร้างเอกสาร'); }

      // ขั้นตอนที่ 2: อ่านเนื้อหาจาก Backend
      if (P) { P.setStage('read', 'active', 'กำลังเชื่อมต่อเซิร์ฟเวอร์อ่านไฟล์...'); }
      currentStage = 'read';
      var result = await analyzeDocument(file);
      window.lastResult = result;

      if (P) {
        P.setStage('read', 'done', 'อ่านได้ ' + (result.blocks ? result.blocks.length : 0) + ' ส่วน');
        P.setStage('analyze', 'active', 'กำลังจัดโครงสร้าง...');
      }
      currentStage = 'analyze';

      // ขั้นตอนที่ 3: สกัดข้อมูลด้วย EthicExtractor
      var found = {};
      if (window.EthicExtractor && result.blocks) {
        found = window.EthicExtractor.extract(result.blocks);
      }
      
      // ใช้เฉพาะสิ่งที่สกัดได้จากไฟล์นี้ (ไม่เก็บค่าจากไฟล์ครั้งก่อน)
      DATA = found;
      DRAFT = {};
      var n = Object.keys(found).length;

      if (P) {
        P.setStage('analyze', n ? 'done' : 'warning',
          n ? 'จัดเข้าฟอร์มได้ ' + n + ' ช่อง'
            : 'ไฟล์นี้ไม่ได้เรียงตามฟอร์ม AP 02 ระบบจึงจับคู่ช่องอัตโนมัติไม่ได้ (ไม่ใช่ข้อผิดพลาด) กดปุ่ม "ให้ AI ช่วยกรอก" หรือกรอกเอง');
      }

      // ขั้นตอนที่ 4: ผลตรวจจุดสงสัยมากับ /analyze แล้ว (rule-based ยังไม่ใช่ AI)
      var suspects = result.suspects || [];
      var sm = result.summary || {};
      window.lastSuspects = suspects;
      if (P) {
        P.setStage('language', 'done', suspects.length
          ? 'พบ ' + suspects.length + ' จุดสงสัย (แดง ' + (sm.red_count || 0) + ' / เหลือง ' + (sm.yellow_count || 0) + ')'
          : 'ไม่พบจุดสงสัย');
      }

      if (window.EthicSuspects) { window.EthicSuspects.render(suspects, result.blocks); }

      
      currentStage = 'layout';
      await renderVariants(P, true);

    } catch (err) {
      if (P && currentStage) { P.setStage(currentStage, 'error', 'ไม่สำเร็จ'); }
      $('status').textContent = 'สร้างเอกสารไม่สำเร็จ';
      showError(err && err.message ? err.message : String(err));
    } finally {
      btn.disabled = false;
    }
  }

  // ----------------------------------------------------------------
  // ให้ AI ช่วยกรอกช่องจากไฟล์ (ผู้ใช้ต้องกดและยืนยันเองทุกครั้ง)
  // ----------------------------------------------------------------
  var AI_CONSENT =
    'ระบบจะส่งข้อความจากไฟล์ของคุณไปยังบริการ AI ภายนอก เพื่อให้ AI อ่านและร่างข้อความลงช่องที่เกี่ยวข้อง (ไม่ต้องเรียงหัวข้อตามฟอร์ม)\n\n' +
    '• ปิดบังอัตโนมัติ: อีเมล เบอร์โทร เลขบัตรประชาชน และชื่อที่ขึ้นต้นด้วยคำนำหน้า (นาย นาง ดร. ฯลฯ)\n' +
    '• ปิดบังไม่ได้: ชื่อที่ไม่มีคำนำหน้า ที่อยู่ ชื่อสถานที่ อาจถูกส่งไปด้วย\n\n' +
    'ต้องการดำเนินการต่อหรือไม่?';
  var AI_LOSE_EDITS = 'คุณได้แก้ไขเอกสารในหน้าตัวอย่างไว้แล้ว การให้ AI กรอกจะสร้างเอกสารใหม่ และข้อความที่แก้ไว้จะหายไป\n\nต้องการดำเนินการต่อหรือไม่?';

  async function aiFill() {
    var result = window.lastResult;
    var P = window.EthicProgress;
    if (!result || !result.blocks || !result.blocks.length) {
      showError('ยังไม่มีข้อความจากไฟล์ กรุณากดสร้างเอกสารก่อน');
      return;
    }
    if (!window.confirm(AI_CONSENT)) { return; }
    if (userEdited && !window.confirm(AI_LOSE_EDITS)) { return; }

    var btn = $('btn-ai-fill');
    btn.disabled = true;
    $('status').textContent = 'AI กำลังอ่านและกรอกช่องจากไฟล์...';
    if (P) { P.setStage('analyze', 'active', 'AI กำลังอ่านไฟล์...'); }

    try {
      if (P) { P.setStage('analyze', 'active', 'AI กำลังอ่านและวิเคราะห์ไฟล์ (ไฟล์ยาวอาจใช้ 1-3 นาที)...'); }
      var r = await fillFromAI(result.filename, result.blocks, 'draft');
      window.lastFill = r;   // ไว้ดูผลใน Console: console.table(lastFill.rejected)
      var vals = (r.form && r.form.values) || {};
      var added = 0;
      Object.keys(vals).forEach(function (fid) {
        var v = vals[fid];
        // ไม่ทับค่าที่ระบบจับคู่จากป้ายหัวข้อได้แล้ว
        if (v && (v.status === 'ai_draft' || v.status === 'found') && v.value != null && !(fid in DATA)) {
          DATA[fid] = v.value;
          if (v.status === 'ai_draft') { DRAFT[fid] = v.source_blocks || []; }
          added++;
        }
      });
      var rejected = (r.rejected || []).length;
      var masked = 0;
      Object.keys(r.redaction_summary || {}).forEach(function (k) { masked += r.redaction_summary[k]; });
      var total = Object.keys(DATA).length;

      if (P) {
        P.setStage('analyze', total ? 'done' : 'warning',
          'AI ร่างให้ ' + added + ' ช่อง (สีเหลือง ต้องตรวจทาน)' + (rejected ? ' / ไม่ผ่านการตรวจ ' + rejected + ' รายการ' : ''));
      }
      await renderVariants(P, false);
      $('status').textContent = 'AI ร่างให้ ' + added + ' ช่อง (สีเหลือง = ร่างจาก AI ต้องตรวจทาน เอาเมาส์ชี้เพื่อดูหน้าที่อ้างอิง)' +
        (rejected ? ' ไม่ผ่านการตรวจ ' + rejected + ' รายการ (ยังเป็นสีแดงให้กรอกเอง)' : '') +
        (masked ? ' | ปิดบังข้อมูลส่วนตัวก่อนส่ง ' + masked + ' รายการ' : '') +
        ' | ตัวเลขทุกตัวในร่างมีอยู่ในหน้าที่อ้างอิง แต่ AI อาจสรุปคลาดเคลื่อน โปรดตรวจทานทุกช่องสีเหลือง';
    } catch (err) {
      if (P) { P.setStage('analyze', 'warning', 'AI ช่วยกรอกไม่สำเร็จ (เอกสารเดิมยังอยู่ครบ)'); }
      $('status').textContent = 'AI ช่วยกรอกไม่สำเร็จ';
      showError(err && err.message ? err.message : String(err));
    } finally {
      btn.disabled = false;
    }
  }

  function applyZoom() {
    $('variants').style.zoom = String(parseInt($('zoom').value, 10) / 100);
  }

  // ----------------------------------------------------------------
  // ผูกเหตุการณ์
  // ----------------------------------------------------------------
  Array.prototype.forEach.call(document.querySelectorAll('input[name="lang"]'), function (r) {
    r.addEventListener('change', updatePickSummary);
  });
  $('btn-generate').addEventListener('click', generate);
  $('btn-ai-fill').addEventListener('click', aiFill);
  $('zoom').addEventListener('change', applyZoom);
  $('btn-print').addEventListener('click', function () { window.print(); });
  $('err-close').addEventListener('click', function () { $('errorModal').hidden = true; });

  updatePickSummary();
})();