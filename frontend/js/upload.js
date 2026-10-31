(function () {
  'use strict';

  // ----------------------------------------------------------------
  // ช่องอัปโหลดไฟล์ + ช่องข้อความเพิ่มเติม
  // ขั้นนี้ทำ 2 อย่าง
  //   (1) แสดงชื่อและขนาดไฟล์ที่ผู้ใช้เลือก
  //   (2) นับจำนวนตัวอักษรในช่องข้อความเพิ่มเติม
  // ยังไม่ตรวจชนิดไฟล์ และยังไม่รองรับลากแล้ววาง (ทำในขั้นถัดไป)
  // ----------------------------------------------------------------

  var fileInput  = document.getElementById('fileInput');
  var fileInfo   = document.getElementById('fileInfo');
  var fileName   = document.getElementById('fileName');
  var fileSize   = document.getElementById('fileSize');
  var extraNotes = document.getElementById('extraNotes');
  var notesCount = document.getElementById('notesCount');

  // ถ้าองค์ประกอบหายไป (เช่น แก้ id ใน index.html) ให้หยุดและเตือนใน Console
  // เพื่อไม่ให้ส่วนอื่นของหน้าเว็บพัง
  if (!fileInput || !fileInfo || !fileName || !fileSize || !extraNotes || !notesCount) {
    console.warn('upload.js: ไม่พบองค์ประกอบที่ต้องใช้ กรุณาตรวจ id ใน index.html');
    return;
  }

  // ----------------------------------------------------------------
  // ไฟล์ที่เลือก
  // ----------------------------------------------------------------
  function formatSize(bytes) {
    if (bytes < 1024) { return bytes + ' B'; }
    if (bytes < 1024 * 1024) { return (bytes / 1024).toFixed(1) + ' KB'; }
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  function currentFile() {
    return (fileInput.files && fileInput.files.length) ? fileInput.files[0] : null;
  }

  function showFile(file) {
    // ใช้ textContent เสมอ เพราะชื่อไฟล์เป็นข้อมูลจากผู้ใช้ ห้ามใส่เป็น HTML
    fileName.textContent = file.name;
    fileSize.textContent = formatSize(file.size);
    fileInfo.hidden = false;
  }

  function clearFile() {
    fileName.textContent = '';
    fileSize.textContent = '';
    fileInfo.hidden = true;
  }

  function onFileChange() {
    var file = currentFile();
    if (file) { showFile(file); } else { clearFile(); }
  }

  // ----------------------------------------------------------------
  // ตัวนับตัวอักษรของช่องข้อความเพิ่มเติม
  // (ขีดจำกัด 2000 ตัวอักษรถูกบังคับโดย maxlength ใน index.html)
  // ----------------------------------------------------------------
  function updateNotesCount() {
    notesCount.textContent = String(extraNotes.value.length);
  }

  // ----------------------------------------------------------------
  // ผูกเหตุการณ์
  // ----------------------------------------------------------------
  fileInput.addEventListener('change', onFileChange);
  extraNotes.addEventListener('input', updateNotesCount);

  // ตั้งค่าเริ่มต้นตอนโหลดหน้า (เผื่อเบราว์เซอร์คืนค่าเดิมในช่องข้อความ)
  updateNotesCount();
  onFileChange();

  // ----------------------------------------------------------------
  // ให้ส่วนอื่น (app.js / api.js ในขั้นถัดไป) ขอไฟล์และข้อความไปใช้
  // ----------------------------------------------------------------
  window.EthicUpload = {
    getFile: currentFile,
    getNotes: function () { return extraNotes.value; }
  };
})();