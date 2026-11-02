(function () {
  'use strict';

  // ----------------------------------------------------------------
  // ช่องอัปโหลดไฟล์ (ขั้นที่ 2)
  //   (1) แสดงชื่อและขนาดไฟล์ที่เลือก
  //   (2) นับตัวอักษรในช่องข้อความเพิ่มเติม
  //   (3) ลากแล้ววางไฟล์ลงในกล่องอัปโหลด
  //   (4) ตรวจไฟล์ก่อนรับ: นามสกุล, MIME type, ขนาด, ไฟล์ว่าง, ไบต์แรกของไฟล์
  //   (5) ส่งเหตุการณ์ 'ethic:file' ให้ progress.js ใช้อัปเดตแถบสถานะ
  //
  // หมายเหตุ: การตรวจฝั่งเบราว์เซอร์ช่วยให้ผู้ใช้รู้ปัญหาเร็วเท่านั้น
  // เมื่อมีแบ็กเอนด์ ต้องตรวจซ้ำที่เซิร์ฟเวอร์เสมอ
  // ----------------------------------------------------------------

  // ---------- ค่าตั้งต้น (แก้ได้ที่นี่ที่เดียว) ----------
  var MAX_SIZE_MB = 10;
  var MAX_SIZE = MAX_SIZE_MB * 1024 * 1024;

  var RULES = 
  {
    pdf: 
    {
      mime: ['application/pdf'],
      signature: [0x25, 0x50, 0x44, 0x46]          // "%PDF"
    },
    docx: 
    {
      mime: ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
      signature: [0x50, 0x4B, 0x03, 0x04]          // "PK\3\4" (DOCX คือไฟล์ ZIP)
    }
  };

  // ---------- องค์ประกอบในหน้า ----------
  var uploadBox  = document.getElementById('uploadBox');
  var fileInput  = document.getElementById('fileInput');
  var fileInfo   = document.getElementById('fileInfo');
  var fileName   = document.getElementById('fileName');
  var fileSize   = document.getElementById('fileSize');
  var fileError  = document.getElementById('fileError');
  var extraNotes = document.getElementById('extraNotes');
  var notesCount = document.getElementById('notesCount');

  if (!uploadBox || !fileInput || !fileInfo || !fileName || !fileSize || !fileError || !extraNotes || !notesCount) 
  {
    console.warn('upload.js: ไม่พบองค์ประกอบที่ต้องใช้ กรุณาตรวจ id ใน index.html');
    return;
  }

  // ไฟล์ที่ผ่านการตรวจแล้วเท่านั้น (ส่วนอื่นจะเห็นเฉพาะไฟล์นี้)
  var validFile = null;
  // ใช้กันผลตรวจเก่าที่เสร็จช้ากว่า เมื่อผู้ใช้เลือกไฟล์ใหม่ระหว่างตรวจอยู่
  var checkToken = 0;

  // ----------------------------------------------------------------
  // ตัวช่วย
  // ----------------------------------------------------------------
  function formatSize(bytes) 
  {
    if (bytes < 1024)
    { 
      return bytes + ' B'; 
    }
    if (bytes < 1024 * 1024) 
    { 
      return (bytes / 1024).toFixed(1) + ' KB'; 
    }
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  function getExtension(name) 
  {
    var i = name.lastIndexOf('.');
    return i < 0 ? '' : name.slice(i + 1).toLowerCase();
  }

  // ประกาศเหตุการณ์ให้ไฟล์อื่น (progress.js) รับรู้
  // status: 'checking' | 'valid' | 'rejected' | 'cleared'
  function emit(status, file, message) 
  {
    document.dispatchEvent(new CustomEvent('ethic:file', 
      {
      detail: { status: status, file: file || null, message: message || '' }
      }));
  }

  // ----------------------------------------------------------------
  // แสดงผลบนหน้า (ใช้ textContent เสมอ เพราะชื่อไฟล์มาจากผู้ใช้)
  // ----------------------------------------------------------------
  function showFile(file) 
  {
    fileName.textContent = file.name;
    fileSize.textContent = formatSize(file.size);
    fileInfo.hidden = false;
  }

  function hideFile() 
  {
    fileName.textContent = '';
    fileSize.textContent = '';
    fileInfo.hidden = true;
  }

  function showError(msg) 
  {
    fileError.textContent = msg;
    fileError.hidden = false;
  }

  function hideError() 
  {
    fileError.textContent = '';
    fileError.hidden = true;
  }

  // ----------------------------------------------------------------
  // การตรวจไฟล์ ส่งข้อความผิดพลาดกลับเป็นข้อความ หรือ '' ถ้าผ่าน
  // ----------------------------------------------------------------
  function checkBasics(file) {
    var ext = getExtension(file.name);

    if (!RULES[ext]) 
    {
      var hint = (ext === 'doc') ? ' (ไฟล์ .doc รุ่นเก่า ให้เปิดใน Word แล้วบันทึกเป็น .docx ก่อน)' : '';
      return (ext ? 'ไม่รองรับไฟล์ชนิด .' + ext : 'ไม่รองรับไฟล์ที่ไม่มีนามสกุล') + ' รองรับเฉพาะ PDF และ DOCX' + hint;
    }
    if (file.size === 0) 
    {
      return 'ไฟล์นี้ว่างเปล่า (0 B) กรุณาเลือกไฟล์อื่น';
    }
    if (file.size > MAX_SIZE) 
    {
      return 'ไฟล์มีขนาด ' + formatSize(file.size) + ' เกินขีดจำกัด ' + MAX_SIZE_MB + ' MB';
    }
    // บางระบบไม่ส่ง MIME มา (ค่าว่าง) จึงตรวจเฉพาะเมื่อมีค่า
    var t = file.type;
    if (t && t !== 'application/octet-stream' && RULES[ext].mime.indexOf(t) < 0) 
    {
      return 'ชนิดของไฟล์ (' + t + ') ไม่ตรงกับนามสกุล .' + ext;
    }
    return '';
  }

  // อ่านไบต์แรกของไฟล์เทียบกับลายเซ็นของ PDF / ZIP(DOCX)
  function checkSignature(file) 
  {
    var ext = getExtension(file.name);
    var sig = RULES[ext].signature;
    return file.slice(0, sig.length).arrayBuffer().then(function (buf) 
    {
      var bytes = new Uint8Array(buf);
      for (var i = 0; i < sig.length; i++) 
      {
        if (bytes[i] !== sig[i]) 
        {
          return 'เนื้อไฟล์ไม่ตรงกับนามสกุล .' + ext + ' ไฟล์อาจเสียหาย หรือถูกเปลี่ยนนามสกุลมา';
        }
      }
      return '';
    }).catch(function () {
      return 'อ่านไฟล์ไม่ได้ ไฟล์อาจเสียหายหรือถูกย้ายไปแล้ว กรุณาเลือกใหม่';
    });
  }

  // ----------------------------------------------------------------
  // ขั้นตอนหลัก: รับไฟล์ -> ตรวจ -> ยอมรับหรือปฏิเสธ
  // fromDrop = true เมื่อมาจากการลากวาง (ต้องใส่ไฟล์ลงช่อง input เอง)
  // ----------------------------------------------------------------
  function reject(msg) 
  {
    validFile = null;
    fileInput.value = '';          // ล้างช่องเลือกไฟล์ ไม่ให้ค้างไฟล์ที่ไม่ผ่าน
    hideFile();
    showError(msg);
    emit('rejected', null, msg);
  }

  function accept(file, fromDrop) 
  {
    if (fromDrop) 
    {
      try 
      {
        var dt = new DataTransfer();
        dt.items.add(file);
        fileInput.files = dt.files;
      } 
      catch (e) 
      {
        // เบราว์เซอร์บางตัวไม่ให้กำหนดค่า input เอง: ยังใช้ไฟล์ผ่าน EthicUpload.getFile() ได้
      }
    }
    validFile = file;
    hideError();
    showFile(file);
    emit('valid', file, '');
  }

  function processFile(file, fromDrop) 
  {
    var token = ++checkToken;

    if (!file) 
    {
      validFile = null;
      hideFile();
      hideError();
      emit('cleared', null, '');
      return;
    }

    validFile = null;
    hideFile();
    hideError();
    emit('checking', file, '');

    var basicError = checkBasics(file);
    if (basicError) 
    { 
      reject(basicError); return; 
    }

    checkSignature(file).then(function (sigError) 
    {
      if (token !== checkToken) 
      { 
        return; 
      }   // มีการเลือกไฟล์ใหม่แล้ว ทิ้งผลนี้
      if (sigError) 
      { 
        reject(sigError); 
      } 
      else 
      { 
        accept(file, fromDrop); 
      }
    });
  }

  // ----------------------------------------------------------------
  // เลือกไฟล์ด้วยปุ่ม
  // ----------------------------------------------------------------
  function onFileChange() 
  {
    var f = (fileInput.files && fileInput.files.length) ? fileInput.files[0] : null;
    processFile(f, false);
  }

  // ----------------------------------------------------------------
  // ลากแล้ววาง
  // ----------------------------------------------------------------
  function hasFiles(e) 
  {
    var types = e.dataTransfer && e.dataTransfer.types;
    if (!types) 
    { 
      return false; 
    }
    for (var i = 0; i < types.length; i++) 
    {
      if (types[i] === 'Files') 
      { 
        return true; 
      }
    }
    return false;
  }

  function setDragOver(on) 
  {
    uploadBox.classList.toggle('dragover', on);
  }

  uploadBox.addEventListener('dragenter', function (e) 
  {
    if (!hasFiles(e)) 
    { 
      return; 
    }
    e.preventDefault();
    setDragOver(true);
  });

  uploadBox.addEventListener('dragover', function (e) 
  {
    if (!hasFiles(e)) 
    { 
      return; 
    }
    e.preventDefault();                       // จำเป็น ไม่งั้นจะวางไม่ได้
    e.dataTransfer.dropEffect = 'copy';
    setDragOver(true);
  });

  uploadBox.addEventListener('dragleave', function (e) 
  {
    // ไม่ปิดไฮไลต์ถ้าเมาส์แค่เคลื่อนเข้าองค์ประกอบลูกภายในกล่อง
    if (e.relatedTarget && uploadBox.contains(e.relatedTarget)) 
    { 
      return; 
    }
    setDragOver(false);
  });

  uploadBox.addEventListener('drop', function (e) 
  {
    if (!hasFiles(e)) 
    { 
      return; 
    }
    e.preventDefault();
    setDragOver(false);
    var files = e.dataTransfer.files;
    if (!files || files.length === 0) 
    { 
      return; 
    }
    if (files.length > 1) 
    {
      reject('ลากวางได้ครั้งละ 1 ไฟล์ (คุณลากมา ' + files.length + ' ไฟล์)');
      return;
    }
    processFile(files[0], true);
  });

  // กันเบราว์เซอร์เปิดไฟล์ทิ้งหน้าเว็บ เมื่อผู้ใช้วางไฟล์พลาดนอกกล่อง
  window.addEventListener('dragover', function (e) 
  {
    if (hasFiles(e)) 
    { 
      e.preventDefault(); 
    }
  });
  window.addEventListener('drop', function (e) 
  {
    if (hasFiles(e)) 
    { 
      e.preventDefault(); 
    }
  });

  // ----------------------------------------------------------------
  // ตัวนับตัวอักษรของช่องข้อความเพิ่มเติม (ขีดจำกัดอยู่ที่ maxlength ใน index.html)
  // ----------------------------------------------------------------
  function updateNotesCount() 
  {
    notesCount.textContent = String(extraNotes.value.length);
  }

  // ----------------------------------------------------------------
  // ผูกเหตุการณ์และตั้งค่าเริ่มต้น
  // ----------------------------------------------------------------
  fileInput.addEventListener('change', onFileChange);
  extraNotes.addEventListener('input', updateNotesCount);

  updateNotesCount();
  onFileChange();   // เผื่อเบราว์เซอร์คืนค่าไฟล์เดิมตอนรีเฟรช

  // ให้ส่วนอื่น (app.js / progress.js / api.js) ขอไฟล์และข้อความไปใช้
  // getFile() คืนเฉพาะไฟล์ที่ผ่านการตรวจแล้ว ไม่ผ่านหรือยังตรวจไม่เสร็จจะได้ null
  window.EthicUpload = 
  {
    getFile: function () 
    { 
      return validFile; 
    },
    getNotes: function () 
    { 
      return extraNotes.value; 
    },
    maxSizeMB: MAX_SIZE_MB
  };
})();