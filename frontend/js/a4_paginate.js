/* a4_paginate.js — แบ่งพรีวิว docx-preview เป็นแผ่น A4 แยกกัน + จัดหน้าใหม่อัตโนมัติเมื่อพิมพ์ (เหมือน Word)
 *
 * ลำดับเรียกใน previewTemplate():
 *   renderAsync → TemplateEditor.enable → TemplateCheckbox.enable → await A4Paginate.run(host) → A4Paginate.autoFit(host)
 * (ต้อง run หลัง enable เพราะช่องกรอกเพิ่มความสูงของแถว และ host ต้องไม่ถูก display:none)
 *
 * - ย้าย DOM node เดิม ไม่ clone เนื้อหา → ช่องกรอก/checkbox/event ไม่หาย
 * - ตารางยาวถูกแบ่งตามแถว (shell ที่มี data-a4-id เดียวกัน) และรวมกลับเมื่อจัดหน้าใหม่
 * - หัวข้อสั้น ๆ (เลขข้อ/ตามด้วยตาราง) ไม่ถูกทิ้งโดดเดี่ยวท้ายหน้า (keep-with-next)
 */
(function (root) {
    'use strict';
    var EPS = 1, PAGE_W = 793.7, MAX_CHAIN = 2, REFLOW_DELAY = 220;

    // ───────────── วัดขนาด ─────────────
    function overflows(art) { return art.scrollHeight > art.clientHeight + EPS; }
    function hOf(el) { return el.getBoundingClientRect().height; }

    // ───────────── keep-with-next (Word ใช้ keepNext กับหัวข้อ) ─────────────
    function kwn(el) {
        if (!el || el.tagName !== 'P') { return false; }
        var t = (el.textContent || '').replace(/\s+/g, ' ').trim();
        if (!t || t.length > 140 || el.querySelector('.fill-field[data-fill="item"]')) { return false; }
        var nx = el.nextElementSibling;
        if (nx && nx.tagName === 'TABLE') { return true; }
        return /^\d+(\.\d+)?[.)]?\s+\S/.test(t);            // "4. หัวข้อ", "12.1 หัวข้อ"
    }
    function trailingChain(art, node) {                  // หัวข้อที่อยู่ท้ายหน้าก่อน node และต้องไปด้วยกัน
        var chain = [], p = node.previousElementSibling;
        while (p && chain.length < MAX_CHAIN && kwn(p)) { chain.unshift(p); p = p.previousElementSibling; }
        return chain.length >= art.children.length - 1 ? [] : chain;
    }

    // ───────────── footer: "หน้า X จาก N" ─────────────
    function setFooterNumbers(footer, page, total) {
        var w = document.createTreeWalker(footer, NodeFilter.SHOW_TEXT, null), n, want = null, done = 0;
        while ((n = w.nextNode())) {
            var t = n.nodeValue;
            if (/หน้า|Page/i.test(t) && !/^\s*\d+\s*$/.test(t)) { want = 'p'; if (!/\d/.test(t)) { continue; } }
            if (/จาก|of/i.test(t) && !/^\s*\d+\s*$/.test(t)) { want = 't'; if (!/\d/.test(t)) { continue; } }
            if (/^\s*\d+\s*$/.test(t) && want) { n.nodeValue = t.replace(/\d+/, want === 'p' ? page : total); want = null; done++; }
        }
        return done;
    }

    // ───────────── ตารางที่ถูกแบ่ง ─────────────
    function shellOf(table) {
        var t = table.cloneNode(false), c = table.querySelector(':scope > colgroup');
        if (c) { t.appendChild(c.cloneNode(true)); }
        t.appendChild(document.createElement('tbody'));
        return t;
    }

    // ───────────── สร้างหน้า + วางบล็อก ─────────────
    function layout(host, blocks) {
        var st = host.__a4, wrapper = host.querySelector('.docx-wrapper'), res = { pages: 0, oversized: 0 };
        Array.prototype.slice.call(wrapper.querySelectorAll(':scope > section.docx')).forEach(function (s) { wrapper.removeChild(s); });
        var pages = [], cur;
        function addPage() {
            var s = st.proto.cloneNode(true); wrapper.appendChild(s);
            cur = { sec: s, art: s.querySelector(':scope > article') }; pages.push(cur); return cur;
        }
        function carryTo(node) {                                  // ย้าย node (+หัวข้อที่ต้องไปด้วย) ไปหน้าใหม่
            var chain = trailingChain(cur.art, node);
            cur.art.removeChild(node); chain.forEach(function (c) { cur.art.removeChild(c); });
            addPage(); chain.forEach(function (c) { cur.art.appendChild(c); }); cur.art.appendChild(node);
            return chain.length;
        }
        function place(node) {
            cur.art.appendChild(node);
            if (!overflows(cur.art)) { return; }
            if (cur.art.children.length === 1) { res.oversized++; return; }
            var k = carryTo(node);
            if (overflows(cur.art) && cur.art.children.length === 1 + k) { res.oversized++; }
        }
        function placeTable(tbl) {
            var rows = Array.prototype.slice.call(tbl.rows), t = shellOf(tbl), tb = t.lastChild;
            cur.art.appendChild(t);
            rows.forEach(function (r) {
                tb.appendChild(r);
                if (!overflows(cur.art)) { return; }
                if (tb.rows.length === 1) {                        // แถวแรกของ shell นี้ก็ไม่พอ
                    if (cur.art.children.length > 1) { carryTo(t); if (overflows(cur.art)) { res.oversized++; } }
                    else { res.oversized++; }
                    return;
                }
                tb.removeChild(r);
                t = shellOf(tbl); tb = t.lastChild; addPage(); cur.art.appendChild(t); tb.appendChild(r);
                if (overflows(cur.art)) { res.oversized++; }
            });
        }
        addPage();
        blocks.forEach(function (b) { if (b.tagName === 'TABLE') { placeTable(b); } else { place(b); } });

        var total = pages.length;
        pages.forEach(function (p, i) {
            var f = p.sec.querySelector(':scope > footer');
            if (f) { setFooterNumbers(f, i + 1, total); }
            p.sec.setAttribute('data-page', i + 1);
        });
        res.pages = total;
        st.pages = pages; st.sig = signature(pages);
        return res;
    }

    function signature(pages) {
        return pages.map(function (p) {
            return Array.prototype.map.call(p.art.children, function (c) { return c.tagName === 'TABLE' ? 'T' + c.rows.length : 'p'; }).join('');
        }).join('|');
    }

    // รวมบล็อกจากทุกหน้ากลับเป็นลำดับเดียว (ตารางที่ถูกแบ่งถูกรวมกลับ)
    function collect(host) {
        var blocks = [], masters = {};
        host.querySelectorAll('.docx-wrapper > section.docx > article').forEach(function (art) {
            Array.prototype.slice.call(art.children).forEach(function (c) {
                if (c.tagName === 'TABLE' && c.getAttribute('data-a4-id')) {
                    var id = c.getAttribute('data-a4-id');
                    if (masters[id]) { Array.prototype.slice.call(c.rows).forEach(function (r) { masters[id].tBodies[0].appendChild(r); }); }
                    else { masters[id] = c; blocks.push(c); }
                } else { blocks.push(c); }
            });
        });
        return blocks;
    }

    // ───────────── ย่อ/ขยาย ─────────────
    function applyZoom(host) {
        var w = host.querySelector('.docx-wrapper'); if (!w) { return 1; }
        var cs = getComputedStyle(host);
        var avail = host.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight) - 4;
        var mode = host.__a4Mode || 'fit', z = mode === 'fit' ? Math.min(1, avail / PAGE_W) : mode;
        z = Math.max(0.3, Math.min(2, z)); w.style.zoom = z;
        var lbl = document.getElementById('a4ZoomLabel'); if (lbl) { lbl.textContent = Math.round(z * 100) + '%'; }
        return z;
    }
    function withZoom1(host, fn) {                         // วัดที่ scale 1 เสมอ (zoom ทำให้ rect กับ clientHeight ไม่ตรงกัน)
        var w = host.querySelector('.docx-wrapper'), z = w ? w.style.zoom : '';
        if (w) { w.style.zoom = ''; }
        try { return fn(); } finally { if (w) { w.style.zoom = z; } }
    }
    function setZoom(host, mode) { host.__a4Mode = mode; return applyZoom(host); }

    // ───────────── จัดหน้าใหม่ตอนพิมพ์ ─────────────
    function needsReflow(host) {
        var st = host.__a4, arts = st.pages.map(function (p) { return p.art; }), i, art;
        for (i = 0; i < arts.length; i++) { if (overflows(arts[i])) { return true; } }
        if (st.blockedSig === signature(st.pages)) { return false; }
        for (i = 0; i < arts.length - 1; i++) {                 // เนื้อหาหด → ดึงบล็อกแรกของหน้าถัดไปกลับมาได้ไหม
            art = arts[i];
            var first = arts[i + 1].firstElementChild; if (!first) { continue; }
            var last = art.lastElementChild;
            var used = last ? last.getBoundingClientRect().bottom - art.getBoundingClientRect().top : 0;
            var free = art.clientHeight - used;
            var need = first.tagName === 'TABLE' ? hOf(first.rows[0]) : hOf(first);
            if (kwn(first) && first.nextElementSibling) {
                var sec = first.nextElementSibling; need += sec.tagName === 'TABLE' ? hOf(sec.rows[0]) : hOf(sec);
            }
            if (free > need + EPS) { return true; }
        }
        return false;
    }

    function reflow(host) {
        var st = host.__a4;
        return withZoom1(host, function () {
            if (!needsReflow(host)) { return null; }
            var act = document.activeElement, sel = getSelection(), saved = null;
            if (act && host.contains(act) && sel.rangeCount) {
                saved = { a: sel.anchorNode, ao: sel.anchorOffset, f: sel.focusNode, fo: sel.focusOffset };
            }
            var before = st.sig, top = host.scrollTop, wy = window.scrollY;
            var res = layout(host, collect(host));
            if (st.sig === before) { st.blockedSig = st.sig; } else { st.blockedSig = null; }
            if (saved && act.isConnected) {
                act.focus({ preventScroll: true });
                try { sel.setBaseAndExtent(saved.a, saved.ao, saved.f, saved.fo); } catch (e) { /* ignore */ }
            }
            host.scrollTop = top; window.scrollTo(window.scrollX, wy);
            return res;
        });
    }

    function bindReflow(host) {
        if (host.__a4Bound) { return; }
        host.__a4Bound = true;
        var timer = null, composing = false;
        function schedule() {
            clearTimeout(timer);
            timer = setTimeout(function () { if (!composing) { reflow(host); applyZoom(host); } }, REFLOW_DELAY);
        }
        host.addEventListener('input', schedule);
        host.addEventListener('compositionstart', function () { composing = true; });     // พิมพ์ไทย/IME: ไม่ย้าย DOM ระหว่างพิมพ์
        host.addEventListener('compositionend', function () { composing = false; schedule(); });
        host.addEventListener('tplcheckbox-change', schedule);
    }

    // ───────────── ป้ายเลขหน้าลอย (ไม่ใช่ footer ของกระดาษ) ─────────────
    var BADGE_RE = /^หน้า\s*\d+\s*(จาก|\/)\s*\d+$/;
    function purgeFloatingBadges(scope) {
        var n = 0;
        scope.querySelectorAll('*').forEach(function (el) {
            if (el.children.length || !BADGE_RE.test((el.textContent || '').trim())) { return; }
            if (el.closest('section.docx > footer, section.docx > header, article, .fill-field')) { return; }
            el.remove(); n++;
        });
        return n;
    }
    function watchBadges(host) {
        var scope = host.closest('section') || host.parentNode;
        if (scope.__a4Watch) { return; }
        scope.__a4Watch = true;
        purgeFloatingBadges(scope);
        if (window.MutationObserver) { new MutationObserver(function () { purgeFloatingBadges(scope); }).observe(scope, { childList: true, subtree: true }); }
    }

    // ───────────── API ─────────────
    async function run(host) {
        var result = { pages: 0, oversized: 0 };
        if (!host.getClientRects().length) {
            result.skipped = 'hidden';
            console.warn('A4Paginate: #templatePreview ยังซ่อนอยู่ — แสดง section ก่อนเรียก run()');
            return result;
        }
        var wrapper = host.querySelector('.docx-wrapper'), secs = host.querySelectorAll('.docx-wrapper > section.docx');
        if (!wrapper || secs.length !== 1) { result.pages = secs.length; result.skipped = 'already'; return result; }
        if (document.fonts && document.fonts.ready) { await document.fonts.ready; }

        var src = secs[0], article = src.querySelector(':scope > article');
        var proto = src.cloneNode(true); proto.querySelector(':scope > article').innerHTML = '';
        host.__a4 = { proto: proto, pages: [], sig: '', blockedSig: null };

        var blocks = Array.prototype.slice.call(article.children), tid = 0;
        blocks.forEach(function (b) { if (b.tagName === 'TABLE') { b.setAttribute('data-a4-id', 't' + (tid++)); } });
        article.innerHTML = '';
        wrapper.appendChild(src);                               // src ยังอยู่ใน DOM; layout() จะลบทุก section ออกก่อนสร้างใหม่
        var res = layout(host, blocks);
        bindReflow(host); watchBadges(host);
        return res;
    }

    function autoFit(host) {
        if (!host.__a4Mode) { host.__a4Mode = 'fit'; }
        if (!document.getElementById('a4ZoomBar')) {
            var bar = document.createElement('div');
            bar.id = 'a4ZoomBar';
            bar.style.cssText = 'display:flex;gap:6px;align-items:center;justify-content:flex-end;margin:0 0 8px;font-size:13px';
            bar.innerHTML = '<button type="button" data-z="-">−</button><span id="a4ZoomLabel" style="min-width:3em;text-align:center"></span>' +
                '<button type="button" data-z="+">+</button><button type="button" data-z="fit">พอดีกว้าง</button><button type="button" data-z="1">100%</button>';
            bar.querySelectorAll('button').forEach(function (b) { b.style.cssText = 'border:1px solid #e5e7eb;background:#fff;border-radius:6px;padding:4px 10px;cursor:pointer'; });
            bar.addEventListener('click', function (e) {
                var b = e.target.closest('button'); if (!b) { return; }
                var cur = parseFloat(host.querySelector('.docx-wrapper').style.zoom) || 1, k = b.getAttribute('data-z');
                setZoom(host, k === 'fit' ? 'fit' : k === '1' ? 1 : Math.round((cur + (k === '+' ? 0.1 : -0.1)) * 100) / 100);
            });
            host.parentNode.insertBefore(bar, host);
        }
        if (!host.__a4Obs) {
            host.__a4Obs = true;
            if (window.ResizeObserver) { new ResizeObserver(function () { applyZoom(host); }).observe(host); }
            else { window.addEventListener('resize', function () { applyZoom(host); }); }
        }
        return applyZoom(host);
    }

    root.A4Paginate = { run: run, autoFit: autoFit, setZoom: setZoom, reflow: reflow, purgeFloatingBadges: purgeFloatingBadges };
})(window);