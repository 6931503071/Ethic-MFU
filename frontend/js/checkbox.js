    /*
    * checkbox.js - แปลงสัญลักษณ์ช่องสี่เหลี่ยม (☐) ในพรีวิว docx ให้คลิกติ๊กได้
    * ใช้: TemplateCheckbox.enable(host) หลัง docx.renderAsync เสร็จ
    *
    * หลักการรักษา layout: ไม่เปลี่ยนตัวอักษร ☐ เป็น ☑ (สองตัวนี้กว้างไม่เท่ากัน)
    * แต่คงตัว ☐ ไว้เสมอ แล้ววางเครื่องหมาย ✓ ทับด้วย CSS (::after) ความกว้างบรรทัดจึงไม่เปลี่ยน
    */
    (function (root) {
    'use strict';

    // สัญลักษณ์ที่ถือว่าเป็น "ช่องว่าง" และ "ติ๊กแล้ว" (เพิ่มได้ที่นี่)
    // \uF0A8, \uF06F, \uF071 = กล่องจาก Wingdings; \uF0FE, \uF0FD = ☑ ☒ จาก Wingdings
    var EMPTY   = '\u2610\u25A1\u274F\u2751\uF0A8\uF06F\uF071';
    var CHECKED = '\u2611\u2612\uF0FE\uF0FD';
    var BOX_RE  = new RegExp('[' + EMPTY + CHECKED + ']', 'g');
    var ANY_BOX = new RegExp('[' + EMPTY + CHECKED + ']');

    var CSS =
        '.tpl-cb{position:relative;display:inline-block;cursor:pointer;user-select:none;}' +
        '.tpl-cb:hover{background:#eff6ff;}' +
        '.tpl-cb:focus-visible{outline:2px solid #3b82f6;outline-offset:1px;}' +
        '.tpl-cb--sym{font-family:"Segoe UI Symbol","MS Gothic","Noto Sans Symbols2",sans-serif;}' +
        '.tpl-cb::after{content:"";position:absolute;left:0;right:0;top:0;text-align:center;' +
        'color:#000;font-weight:normal;font-family:"Segoe UI Symbol","MS Gothic",sans-serif;}' +
        '.tpl-cb[data-checked="true"]::after{content:"\\2713";}';

    function injectCss() {
        if (document.getElementById('tplCheckboxCss')) { return; }
        var st = document.createElement('style');
        st.id = 'tplCheckboxCss';
        st.textContent = CSS;
        document.head.appendChild(st);
    }

    function makeBox(ch) {
        var el = document.createElement('span');
        el.className = 'tpl-cb' + (ch.charCodeAt(0) >= 0xF000 ? ' tpl-cb--sym' : '');
        el.textContent = '\u2610';                       // แสดงเป็น ☐ เสมอ
        el.setAttribute('role', 'checkbox');
        el.setAttribute('tabindex', '0');
        setState(el, CHECKED.indexOf(ch) >= 0);          // ถ้าต้นฉบับติ๊กไว้อยู่แล้ว ให้เริ่มเป็นติ๊ก
        return el;
    }

    function setState(el, checked) {
        el.setAttribute('data-checked', checked ? 'true' : 'false');
        el.setAttribute('aria-checked', checked ? 'true' : 'false');
    }

    function indexOf(host, el) {
        return Array.prototype.indexOf.call(host.querySelectorAll('.tpl-cb'), el);
    }

    function toggle(host, el) {
        var next = el.getAttribute('data-checked') !== 'true';
        setState(el, next);
        host.dispatchEvent(new CustomEvent('tplcheckbox-change', {
        bubbles: true, detail: { index: indexOf(host, el), checked: next }
        }));
    }

    // แยก text node ที่มี ☐ ออกเป็น text + <span.tpl-cb> + text
    function wrapTextNode(node) {
        var text = node.nodeValue, re = new RegExp(BOX_RE.source, 'g');
        var frag = document.createDocumentFragment(), last = 0, m, found = false;
        while ((m = re.exec(text)) !== null) {
        found = true;
        if (m.index > last) { frag.appendChild(document.createTextNode(text.slice(last, m.index))); }
        frag.appendChild(makeBox(m[0]));
        last = m.index + 1;
        }
        if (!found) { return 0; }
        if (last < text.length) { frag.appendChild(document.createTextNode(text.slice(last))); }
        node.parentNode.replaceChild(frag, node);
        return 1;
    }

    /** เรียกหลัง docx.renderAsync เสร็จ คืนจำนวนช่องที่แปลง */
    function enable(host) {
        if (!host) { return 0; }
        injectCss();

        // เก็บ text node ไว้ก่อน แล้วค่อยแก้ (กัน DOM เปลี่ยนระหว่างเดิน)
        var walker = document.createTreeWalker(host, NodeFilter.SHOW_TEXT, null);
        var nodes = [], n;
        while ((n = walker.nextNode())) {
        if (ANY_BOX.test(n.nodeValue) && !(n.parentNode.closest && n.parentNode.closest('.tpl-cb'))) {
            nodes.push(n);
        }
        }
        nodes.forEach(wrapTextNode);

        // ผูก event ครั้งเดียวต่อ host (event delegation)
        if (!host.__tplCbBound) {
        host.__tplCbBound = true;
        host.addEventListener('mousedown', function (e) {
            if (e.target.closest && e.target.closest('.tpl-cb')) { e.preventDefault(); }  // กัน caret/เลือกข้อความ
        });
        host.addEventListener('click', function (e) {
            var el = e.target.closest && e.target.closest('.tpl-cb');
            if (el && host.contains(el)) { toggle(host, el); }
        });
        host.addEventListener('keydown', function (e) {
            var el = e.target.closest && e.target.closest('.tpl-cb');
            if (el && (e.key === ' ' || e.key === 'Enter')) { e.preventDefault(); toggle(host, el); }
        });
        }
        return host.querySelectorAll('.tpl-cb').length;
    }

    /** คืนสถานะทุกช่องเรียงตามลำดับในเอกสาร เช่น [true,false,false] (ไว้ส่งให้ export DOCX) */
    function getStates(host) {
        return Array.prototype.map.call(host.querySelectorAll('.tpl-cb'), function (el) {
        return el.getAttribute('data-checked') === 'true';
        });
    }

    /** ตั้งสถานะกลับตามลำดับ (ไว้กู้ค่าที่กรอกไว้) */
    function setStates(host, arr) {
        Array.prototype.forEach.call(host.querySelectorAll('.tpl-cb'), function (el, i) {
        if (typeof arr[i] === 'boolean') { setState(el, arr[i]); }
        });
    }

    root.TemplateCheckbox = { enable: enable, getStates: getStates, setStates: setStates };
    })(window);