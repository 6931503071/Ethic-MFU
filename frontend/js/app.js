(function () {
  'use strict';

  // ----------------------------------------------------------------
  // ตั้งค่า
  // ----------------------------------------------------------------
  var TEMPLATE_URL = '../templates/ap02.json';   // เปิดผ่าน Live Server ที่โฟลเดอร์ Ethic MFU
  var template = null;
  var lang = 'th';
  var activeVariant = 0;

  // ----------------------------------------------------------------
  // ข้อความที่ระบบสร้างเอง แยกตามภาษา (ภาษาที่เลือกจะไม่ปนกับอีกภาษา)
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
  // ข้อมูลตัวอย่างจำลอง (ภายหลังจะมาจาก AI ที่อ่านไฟล์ผู้ใช้)
  // รูปแบบ [[ข้อความ|คำอธิบาย]] = ข้อความกำกวม/ผิด แสดงเป็นสีแดง
  // ----------------------------------------------------------------
  var SAMPLE = {
    th: {
      title_th: 'ผลของโปรแกรมออกกำลังกายต่อระดับความเครียดของนักศึกษามหาวิทยาลัย',
      title_en: 'Effects of an Exercise Program on Stress Levels Among University Students',
      field_of_study: 'สาธารณสุขศาสตร์',
      location: 'สถาบันเดียว ณ ห้องปฏิบัติการวิจัยสุขภาพ อาคารเรียนรวม',
      background: 'ความเครียดเป็นปัญหาที่พบบ่อยในนักศึกษา [[กลุ่มตัวอย่างบางส่วน|ระบุจำนวนและเกณฑ์คัดเลือกกลุ่มตัวอย่างให้ชัดเจน]] จะได้รับการประเมินด้วยแบบสอบถามมาตรฐาน',
      objective_primary: ['เพื่อศึกษาผลของโปรแกรมออกกำลังกายต่อระดับความเครียดของนักศึกษา'],
      objective_secondary: ['เพื่อเปรียบเทียบระดับความเครียดก่อนและหลังการออกกำลังกาย'],
      study_design: 'การวิจัยกึ่งทดลองแบบกลุ่มเดียววัดก่อนและหลัง (one-group pretest-posttest design)'
    },
    en: {
      title_th: 'ผลของโปรแกรมออกกำลังกายต่อระดับความเครียดของนักศึกษามหาวิทยาลัย',
      title_en: 'Effects of an Exercise Program on Stress Levels Among University Students',
      field_of_study: 'Public Health',
      location: 'Single center; Health Research Laboratory, Main Academic Building',
      background: 'Stress is a common problem among university students. [[Some participants|Specify the number and selection criteria of participants clearly]] will be assessed with a standardized questionnaire.',
      objective_primary: ['To examine the effect of an exercise program on stress levels among students'],
      objective_secondary: ['To compare stress levels before and after exercise'],
      study_design: 'Quasi-experimental one-group pretest-posttest design'
    }
  };
  // ส่วนเรื่องเฉพาะ A-G: false = ไม่ใช่ (ตัดส่วนนี้ออก)
  ['a', 'b', 'c', 'd', 'e', 'f', 'g'].forEach(function (k) {
    SAMPLE.th['special_' + k + '_applies'] = false;
    SAMPLE.en['special_' + k + '_applies'] = false;
  });

  // ----------------------------------------------------------------
  // 4 แบบที่แตกต่างกัน (โครงสร้างการจัดวาง / การเว้นระยะ / การสรุปความ)
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
  // ตัวช่วยทั่วไป
  // ----------------------------------------------------------------
  function $(id) { return document.getElementById(id); }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) { e.className = cls; }
    if (text !== undefined && text !== null) { e.textContent = text; }
    return e;
  }

  // อ่านข้อความตามภาษาที่เลือก: key_en สำหรับอังกฤษ, key สำหรับไทย
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

  function dv(id) { return (SAMPLE[lang] || {})[id]; }

  function ph(text) { return el('span', 'ph', text); }

  function blockPh(text) {
    var d = el('div', 'para');
    d.appendChild(ph(text));
    return d;
  }

  // ใส่ข้อความ พร้อมแปลง [[ข้อความ|คำอธิบาย]] เป็นข้อความสีแดง
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

  function findField(id) {
    var found = null;
    (function walk(secs) {
      secs.forEach(function (s) {
        (s.fields || []).forEach(function (f) { if (f.id === id) { found = f; } });
        walk(s.subsections || []);
      });
    })(template.sections);
    return found;
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

  // คืนอาร์เรย์ของ node (แต่ละ node แบ่งหน้าได้อิสระ)
  function renderValue(f) {
    var nodes = [], t = f.type, label = tx(f, 'label'), data = dv(f.id);

    if (t === 'text' || t === 'textarea') {
      var p = el('div', 'para');
      if (f.fill_by === 'user') { p.appendChild(ph(S[lang].fill(label))); }
      else if (typeof data === 'string' && data) { richInto(p, data); }
      else { p.appendChild(ph(S[lang].notFound)); }
      nodes.push(p);

    } else if (t === 'numbered_list' || t === 'bullet_list') {
      var items = Array.isArray(data) ? data : [];
      var n = Math.max(items.length, f.min_items || 2);
      for (var i = 0; i < n; i++) {
        var row = el('div', 'item');
        row.appendChild(el('span', 'mk', t === 'numbered_list' ? (i + 1) + '.' : '-'));
        var c = el('span', 'tx');
        if (items[i]) { richInto(c, items[i]); }
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
  // วางช่อง/หัวข้อเป็น "บล็อก" ตามรูปแบบของแต่ละแบบ
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
    var gv = gate ? dv(gate.id) : undefined;
    if (gate && opts.optional === 'omit' && gv === false) { return; }

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
    if (!(gate && gv === false)) {
      var fields = sec.fields || [];
      fields.forEach(function (f) {
        var skip = opts.hideInstructions && fields.length === 1 && (f.type === 'text' || f.type === 'textarea');
        pushField(f, opts, local, skip);
      });
      (sec.subsections || []).forEach(function (s) { pushSection(s, depth + 1, opts, local); });
    }

    // หัวข้อแม่ที่ไม่เหลือเนื้อหาย่อยเลย (เช่น 12.2 เมื่อตัด A-G หมด) ไม่ต้องแสดง
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
  // แบ่งหน้า A4 + header/footer + เลขหน้า
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

  // คืนจำนวนบล็อกที่ใหญ่เกิน 1 หน้า (ไว้เตือน)
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
          // หัวข้อที่ค้างท้ายหน้าให้ย้ายไปหน้าถัดไปพร้อมเนื้อหา
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
  // โหลด template, แจ้งข้อผิดพลาด, ควบคุมหน้าจอ
  // ----------------------------------------------------------------
  function showError(msg) {
    $('err-msg').textContent = msg;
    $('error-modal').hidden = false;
  }

  function loadTemplate() {
    if (location.protocol === 'file:') {
      return Promise.reject(new Error('ไม่สามารถเปิดไฟล์ตรงๆ ได้ กรุณาเปิดผ่าน Live Server (กด Go Live) เพราะเบราว์เซอร์บล็อกการอ่านไฟล์ JSON'));
    }
    return fetch(TEMPLATE_URL, { cache: 'no-store' }).then(function (res) {
      if (!res.ok) {
        throw new Error('โหลด templates/ap02.json ไม่ได้ (รหัส ' + res.status + ')\nตรวจว่าไฟล์อยู่ที่ templates\\ap02.json และเปิด Live Server จากโฟลเดอร์ Ethic MFU (ไม่ใช่เฉพาะโฟลเดอร์ frontend)');
      }
      return res.json();
    }).then(function (data) {
      if (!data.sections || !data.sections.length) { throw new Error('โครงสร้างของ ap02.json ไม่ถูกต้อง (ไม่มี sections)'); }
      if (!data.languages_available || data.languages_available.indexOf('en') < 0) {
        throw new Error('ap02.json ยังไม่ใช่ฉบับสองภาษา กรุณาเขียนทับด้วยไฟล์ฉบับล่าสุด');
      }
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

  async function generate() {
    var btn = $('btn-generate');
    btn.disabled = true;
    $('status').textContent = 'กำลังสร้างเอกสาร...';
    try {
      lang = selectedLang();
      document.documentElement.lang = lang;
      if (!template) { await loadTemplate(); }
      if (document.fonts && document.fonts.ready) { await document.fonts.ready; }

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
        totalOversize += res.oversize;

        var tab = el('button', 'tab', v.name + ' (' + res.pages + ' หน้า)');
        tab.type = 'button';
        tab.setAttribute('role', 'tab');
        (function (idx) { tab.addEventListener('click', function () { activate(idx); }); })(i);
        tabs.appendChild(tab);
      }
      activate(0);
      applyZoom();
      var langName = lang === 'en' ? 'ภาษาอังกฤษ' : 'ภาษาไทย';
      $('status').textContent = 'สร้างเอกสาร' + langName + 'ครบ 4 แบบแล้ว เลือกดูได้จากแท็บด้านล่าง'
        + (totalOversize ? ' (พบ ' + totalOversize + ' ส่วนที่ยาวเกิน 1 หน้า อาจถูกตัดท้าย)' : '');
      $('result').scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (err) {
      $('status').textContent = 'สร้างเอกสารไม่สำเร็จ';
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
  $('zoom').addEventListener('change', applyZoom);
  $('btn-print').addEventListener('click', function () { window.print(); });
  $('err-close').addEventListener('click', function () { $('error-modal').hidden = true; });
  updatePickSummary();
})();
