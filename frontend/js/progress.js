(function () 
{
  'use strict';

  // ----------------------------------------------------------------
  // แถบสถานะการประมวลผล (#progressPanel)
  //
  // ขั้นนี้ทำเฉพาะสิ่งที่ "มีตัวทำงานจริงแล้ว" คือขั้นที่ 1 (ตรวจสอบชนิดและขนาดไฟล์)
  //   - ฟังเหตุการณ์ 'ethic:file' ที่ upload.js ส่งมา แล้วเปลี่ยนสถานะขั้นที่ 1
  //   - ขั้นที่ 2-5 แสดงเป็น "ยังไม่เปิดใช้งาน" จนกว่าจะมีแบ็กเอนด์/AI มาทำงานจริง
  //     เพื่อไม่ให้ผู้ใช้เข้าใจผิดว่าระบบอ่านหรือวิเคราะห์ไฟล์แล้ว
  //
  // สถานะที่ใช้ได้ (ตรงกับ CSS ใน style.css ผ่าน data-state)
  //   pending (ไม่ใส่ data-state) | active | done | error
  //
  // ตอนเพิ่มขั้นถัดไป ให้เปลี่ยน enabled ของขั้นนั้นเป็น true ด้านล่าง
  // แล้วให้โค้ดของขั้นนั้นเรียก EthicProgress.setStage(...) / EthicProgress.fail(...)
  // ----------------------------------------------------------------

  var STAGE_CONFIG = 
  {
    validate: { enabled: true  },
    read:     { enabled: false },
    analyze:  { enabled: false },
    language: { enabled: false },
    layout:   { enabled: false }
  };

  var NOT_READY_TEXT = 'ยังไม่เปิดใช้งาน';
  var VALID_STATES = ['pending', 'active', 'done', 'error'];

  // ---------- องค์ประกอบในหน้า ----------
  var panel        = document.getElementById('progressPanel');
  var list         = document.getElementById('stageList');
  var errorBox     = document.getElementById('errorBox');
  var errorStage   = document.getElementById('errorStage');
  var errorMessage = document.getElementById('errorMessage');
  var retryBtn     = document.getElementById('retryBtn');

  // ต้องมีแค่แผงกับรายการขั้นตอน ส่วนกล่อง error เป็นของเสริม
  if (!panel || !list) 
  {
    console.warn('progress.js: ไม่พบ #progressPanel หรือ #stageList กรุณาตรวจ id ใน index.html');
    return;
  }

  // ----------------------------------------------------------------
  // เตรียมรายการขั้นตอน: เก็บชื่อขั้น และใส่ป้ายข้อความสั้น ๆ ต่อท้ายแต่ละขั้น
  // ----------------------------------------------------------------
  var stages = {};
  var items = list.querySelectorAll('li[data-stage]');

  Array.prototype.forEach.call(items, function (li) 
  {
    var name = li.getAttribute('data-stage');
    var label = li.textContent.trim();      // อ่านก่อนใส่ป้าย จะได้ไม่ปนข้อความป้าย
    var note = document.createElement('span');
    note.className = 'stage-note';
    li.appendChild(note);
    stages[name] = { li: li, note: note, label: label };
  });

  var lastErrorStage = '';

  // ----------------------------------------------------------------
  // ควบคุมสถานะของแต่ละขั้น
  // ----------------------------------------------------------------
  function defaultNote(name) 
  {
    var cfg = STAGE_CONFIG[name];
    return (cfg && cfg.enabled) ? '' : NOT_READY_TEXT;
  }

  function setStage(name, state, noteText) 
  {
    var s = stages[name];
    if (!s) 
    {
      console.warn('progress.js: ไม่รู้จักขั้นตอน "' + name + '"');
      return;
    }
    if (VALID_STATES.indexOf(state) < 0) 
    {
      console.warn('progress.js: สถานะ "' + state + '" ใช้ไม่ได้ (ใช้ได้: ' + VALID_STATES.join(', ') + ')');
      return;
    }

    if (state === 'pending') 
    {
      s.li.removeAttribute('data-state');
    } 
    else 
    {
      s.li.setAttribute('data-state', state);
      panel.hidden = false;
    }
    // ป้าย "ยังไม่เปิดใช้งาน" ใช้เฉพาะตอนรอ ถ้าขั้นนั้นเริ่มทำงานแล้วให้ล้างป้าย
    if (noteText !== undefined) 
    {
      s.note.textContent = noteText;
    } 
    else 
    {
      s.note.textContent = (state === 'pending') ? defaultNote(name) : '';
    }
  }

  function resetStages() 
  {
    Object.keys(stages).forEach(function (name) 
    {
      setStage(name, 'pending');
    });
  }

  // ----------------------------------------------------------------
  // กล่องแจ้งข้อผิดพลาดของขั้นตอน (ใช้ textContent เสมอ)
  // ----------------------------------------------------------------
  function hideError() 
  {
    lastErrorStage = '';
    if (!errorBox) 
    { 
      return; 
    }
    if (errorStage) 
    { 
      errorStage.textContent = ''; 
    }
    if (errorMessage) 
    { 
      errorMessage.textContent = ''; 
    }
    errorBox.hidden = true;
  }

  function showError(name, message) 
  {
    lastErrorStage = name;
    if (!errorBox) 
    { 
      return; 
    }
    var s = stages[name];
    if (errorStage) 
    { 
      errorStage.textContent = 'ขั้นตอน: ' + (s ? s.label : name); 
    }
    if (errorMessage) 
    { 
      errorMessage.textContent = message || 'เกิดข้อผิดพลาด'; 
    }
    errorBox.hidden = false;
  }

  // ให้ขั้นอื่นในอนาคตเรียกใช้ เมื่อขั้นนั้นล้มเหลว
  function fail(name, message) 
  {
    setStage(name, 'error', 'ไม่สำเร็จ');
    showError(name, message);
  }

  function reset() 
  {
    resetStages();
    hideError();
    panel.hidden = true;
  }

  // ----------------------------------------------------------------
  // ปุ่ม "ลองใหม่อีกครั้ง"
  //   ขั้นตรวจไฟล์: เปิดหน้าต่างเลือกไฟล์ใหม่
  //   ขั้นอื่น: ส่งเหตุการณ์ 'ethic:retry' ให้โค้ดของขั้นนั้นรับไปทำเอง
  // ----------------------------------------------------------------
  if (retryBtn) 
  {
    retryBtn.addEventListener('click', function () 
    {
      if (lastErrorStage === 'validate') 
      {
        var fileInput = document.getElementById('fileInput');
        if (fileInput) 
        { 
          fileInput.click(); 
        }
        return;
      }
      document.dispatchEvent(new CustomEvent('ethic:retry', { detail: { stage: lastErrorStage } }));
    });
  }

  // ----------------------------------------------------------------
  // รับเหตุการณ์จาก upload.js
  // status: 'checking' | 'valid' | 'rejected' | 'cleared'
  // ----------------------------------------------------------------
  document.addEventListener('ethic:file', function (e) 
  {
    var d = e.detail || {};

    if (d.status === 'checking') 
    {
      resetStages();
      hideError();
      setStage('validate', 'active', 'กำลังตรวจ...');
    } 
    else if (d.status === 'valid') 
    {
      hideError();
      setStage('validate', 'done', 'ผ่าน');
    } 
    else if (d.status === 'rejected') 
    {
      resetStages();
      fail('validate', d.message);
    } 
    else if (d.status === 'cleared') 
    {
      reset();
    }
  });

  // ตั้งค่าเริ่มต้น: ทุกขั้นเป็น "รอ" และซ่อนแผงไว้จนกว่าผู้ใช้จะเลือกไฟล์
  resetStages();
  hideError();

  window.EthicProgress = 
  {
    setStage: setStage,
    fail: fail,
    reset: reset
  };
}
)
();