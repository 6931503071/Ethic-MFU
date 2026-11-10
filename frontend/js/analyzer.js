/*
 * analyzer.js  -  ขั้นที่ 4: ตรวจคำผิดและปรับภาษาให้เป็นทางการ (แบบใช้กฎ / rule-based)
 *
 * ทำงานโดยไม่ต้องใช้ backend หรือ AI ตรวจได้เฉพาะสิ่งที่ "กฎและพจนานุกรมในไฟล์นี้" รู้จักเท่านั้น
 * คำผิดที่ต้องเข้าใจบริบท (เช่น ใช้คำผิดความหมาย) ต้องรอ AI ในอนาคต
 *
 * หลักการ: ไม่แก้ข้อความเงียบ ๆ แต่ครอบจุดที่พบด้วย [[ข้อความเดิม|คำแนะนำ]]
 * ซึ่ง app.js (richInto) แปลงเป็นข้อความสีแดงอยู่แล้ว ผู้ใช้เห็นคำแนะนำเมื่อเลื่อนเมาส์ไปชี้
 */
(function (root) {
    'use strict';

  // ---------- 1) พจนานุกรมที่แก้ได้เอง: เพิ่มคำได้ที่นี่ ----------
  // คำผิด -> คำที่ถูก (ตรงตัวอักษรเท่านั้น)
    var TYPO = {
    th: {
        'คระกรรมการ': 'คณะกรรมการ',
        'นักศีกษา': 'นักศึกษา',
        'ผลิตภัณฑอาหาร': 'ผลิตภัณฑ์อาหาร',
        'ผู้เขาร่วม': 'ผู้เข้าร่วม',
        'สาธารณะสุข': 'สาธารณสุข',
        'อนุญาติ': 'อนุญาต',
        'ประชาสัมพันธ์ุ': 'ประชาสัมพันธ์'
    },
    en: {
        'recieve': 'receive',
        'seperate': 'separate',
        'occured': 'occurred',
        'participent': 'participant',
        'parcipants': 'participants',
        'questionaire': 'questionnaire',
        'enviroment': 'environment'
    }
    };

  // ภาษาไม่เป็นทางการ -> คำที่เหมาะกับเอกสารทางการ (เป็นข้อเสนอแนะ ไม่ใช่คำผิด)
    var INFORMAL = {
    th: {
        'เยอะ': 'มาก',
        'นิดหน่อย': 'เล็กน้อย',
        'ยังไง': 'อย่างไร',
        'เพราะว่า': 'เนื่องจาก',
        'ก็คือ': 'หมายถึง',
        'อาสาสมัคร': 'ผู้เข้าร่วมการวิจัย (ใช้คำเดียวกันทั้งฉบับ)'
    },
    en: 
    {
        "don't": 'do not',
        "can't": 'cannot',
        "won't": 'will not',
        "doesn't": 'does not',
        "isn't": 'is not',
        'a lot of': 'many / much',
        'kids': 'children'
    }
};

  // ---------- 2) ข้อความที่ "ห้ามแตะ" ----------
  // - จุดที่ถูกครอบ [[...|...]] ไปแล้ว (กันครอบซ้ำ)
  // - ชื่อประกาศ/กฎหมาย ต้องคงถ้อยคำเดิมทุกตัวอักษร
    var LOCKED = new RegExp(
    '\\[\\[.+?\\|.+?\\]\\]' +
    '|ประกาศกระทรวงสาธารณสุข[^\\n]*?พ\\.ศ\\.\\s*\\d{4}' +
    '|Notification of the Ministry of Public Health[^\\n]*?B\\.E\\.\\s*\\d{4}',
    'g'
    );

  // ---------- 3) กฎทั่วไป (regex) ----------
  // category ตรงกับ 8 ประเภทในคำสั่งโปรเจกต์: spelling, encoding, punctuation, ...
    var RULES = [
    { cat: 'encoding', re: /\uFFFD+/g, msg: 'พบอักขระที่แสดงผลไม่ได้ (อาจเป็นปัญหา encoding)' },
    { cat: 'encoding', re: /à¸|à¹|Ã.|â€/g, msg: 'ข้อความเพี้ยน (mojibake) ตรวจสอบ encoding ของไฟล์ต้นฉบับ' },
    { cat: 'spelling', re: /([\u0E31\u0E34-\u0E3A\u0E47-\u0E4E])\1+/g, msg: 'สระ/วรรณยุกต์ซ้ำกัน น่าจะพิมพ์เกิน' },
    { cat: 'spelling', re: /(^|[\s(])[\u0E31\u0E34-\u0E3A\u0E47-\u0E4E]/g, msg: 'สระ/วรรณยุกต์ลอย ไม่มีพยัญชนะนำหน้า', trim: 1 },
    { cat: 'punctuation', re: /\S {2,}/g, msg: 'เว้นวรรคเกิน 1 ช่อง' },
    { cat: 'punctuation', re: /[A-Za-z0-9)] +(?:[,;:!?]|\.(?!\.))/g, msg: 'ไม่ควรเว้นวรรคก่อนเครื่องหมายวรรคตอน', langs: ['en'] },
    { cat: 'punctuation', re: /[,;][A-Za-z]/g, msg: 'ควรเว้นวรรคหลังเครื่องหมายจุลภาค', langs: ['en'] },
    { cat: 'punctuation', re: /\b(\w{2,})\s+\1\b/gi, msg: 'พบคำซ้ำติดกัน', langs: ['en'] },
    { cat: 'punctuation', re: /([,;:!?])\1+/g, msg: 'เครื่องหมายวรรคตอนซ้ำกัน' }
    ];

    function esc(s) { return String(s).replace(/\|/g, '/').replace(/\]\]/g, '] ]'); }

  // หาจุดที่น่าสงสัยใน segment หนึ่ง คืน [{start,end,cat,msg}]
    function scan(seg, lang) {
    var hits = [], k, m, re;

    var typo = TYPO[lang] || {};
    for (k in typo) {
        if (!Object.prototype.hasOwnProperty.call(typo, k)) { continue; }
        var at = seg.indexOf(k);
        while (at >= 0) 
            {
        hits.push({ start: at, end: at + k.length, cat: 'spelling', msg: 'คำผิด แนะนำ: ' + typo[k] });
        at = seg.indexOf(k, at + k.length);
        }
    }

    var inf = INFORMAL[lang] || {};
    for (k in inf) {
        if (!Object.prototype.hasOwnProperty.call(inf, k)) { continue; }
        var src = lang === 'en' ? seg.toLowerCase() : seg;
        var p = src.indexOf(k);
        while (p >= 0) {
        // ภาษาอังกฤษต้องเป็นคำเต็ม (กัน "kids" ไปชนกับคำอื่น) ภาษาไทยไม่มีช่องว่างคั่นคำจึงเทียบตรง ๆ
        var okL = lang !== 'en' || !/[a-z]/i.test(src.charAt(p - 1) || ' ');
        var okR = lang !== 'en' || !/[a-z]/i.test(src.charAt(p + k.length) || ' ');
        if (okL && okR) {
        hits.push({ start: p, end: p + k.length, cat: 'formality', msg: 'ภาษาไม่เป็นทางการ ควรใช้: ' + inf[k] });
        }
        p = src.indexOf(k, p + k.length);
        }
    }

    RULES.forEach(function (r) {
        if (r.langs && r.langs.indexOf(lang) < 0) { return; }
        re = new RegExp(r.re.source, r.re.flags);
        while ((m = re.exec(seg)) !== null) {
        var s = m.index + (r.trim || 0);
        hits.push({ start: s, end: m.index + m[0].length, cat: r.cat, msg: r.msg });
        if (m[0].length === 0) { re.lastIndex++; }
        }
    });
    return hits;
    }

  // ตัดจุดที่ซ้อนทับกัน เก็บอันที่เริ่มก่อน (ถ้าเริ่มพร้อมกันเก็บอันที่ยาวกว่า)
    function dedupe(hits) {
    hits.sort(function (a, b) { return a.start - b.start || (b.end - b.start) - (a.end - a.start); });
    var out = [], lastEnd = -1;
    hits.forEach(function (h) {
        if (h.start >= lastEnd) { out.push(h); lastEnd = h.end; }
    });
    return out;
    }

  // ตรวจข้อความเดียว คืน { text, issues } โดย text มี [[..|..]] ครอบจุดที่พบ
    function checkText(str, lang) {
    if (typeof str !== 'string' || !str) { return { text: str, issues: [] }; }
    lang = lang === 'en' ? 'en' : 'th';

    var out = '', issues = [], last = 0, m;
    var lock = new RegExp(LOCKED.source, 'g');

    function processSegment(seg) {
        var hits = dedupe(scan(seg, lang)), pos = 0, res = '';
        hits.forEach(function (h) {
        res += seg.slice(pos, h.start);
        var orig = seg.slice(h.start, h.end);
        res += '[[' + esc(orig) + '|' + esc(h.msg) + ']]';
        issues.push({ category: h.cat, original: orig, message: h.msg });
        pos = h.end;
        });
        return res + seg.slice(pos);
    }

    while ((m = lock.exec(str)) !== null) {
      out += processSegment(str.slice(last, m.index)) + m[0];   // ส่วนที่ล็อกไว้ใส่กลับตามเดิม
        last = m.index + m[0].length;
    }
    out += processSegment(str.slice(last));
    return { text: out, issues: issues };
    }

  // ตรวจทั้งออบเจ็กต์ (เช่น SAMPLE[lang]) แก้ค่าในที่เดิม ทั้งข้อความและ array ข้อความ
  // คืน { count, byCategory }
    function checkObject(obj, lang) {
    var count = 0, by = {};
    function add(list) {
        list.forEach(function (i) { by[i.category] = (by[i.category] || 0) + 1; });
        count += list.length;
    }
    Object.keys(obj || {}).forEach(function (key) {
        var v = obj[key];
        if (typeof v === 'string') {
        var r = checkText(v, lang); obj[key] = r.text; add(r.issues);
        } else if (Array.isArray(v)) {
        obj[key] = v.map(function (x) {
            if (typeof x !== 'string') { return x; }
            var r = checkText(x, lang); add(r.issues); return r.text;
        });
        }
    });
    return { count: count, byCategory: by };
    }

    root.EthicAnalyzer = { checkText: checkText, checkObject: checkObject };
    if (typeof module !== 'undefined' && module.exports) { module.exports = root.EthicAnalyzer; }
})(typeof window !== 'undefined' ? window : globalThis);