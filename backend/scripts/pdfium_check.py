from pathlib import Path
import pypdfium2 as pdfium
from app.suspects import check_text

def test_read_with_pdfium(pdf_path: str):
    path = Path(pdf_path)
    if not path.exists():
        print(f"ไม่พบไฟล์: {pdf_path}")
        return

    pdf = pdfium.PdfDocument(str(path))
    print(f"--- อ่านไฟล์: {path.name} (จำนวน {len(pdf)} หน้า) ---")
    
    for i, page in enumerate(pdf):
        textpage = page.get_textpage()
        text = textpage.get_text_range()
        print(f"\n[หน้า {i+1}]")
        print("ข้อความที่อ่านได้:")
        print(text[:300] + ("..." if len(text) > 300 else "")) # แสดงตัวอย่าง 300 ตัวอักษรแรก
        
        # ตรวจสอบจุดสงสัยภาษาไทย เช่น สระลอย/ข้อความเพี้ยน
        suspects = check_text(text, page=i+1)
        thai_suspects = [s for s in suspects if s.type in ("THAI_ORPHAN_MARK", "ENCODING_GARBLE")]
        
        print(f"พบจุดสงสัยภาษาไทย/ข้อความเพี้ยน: {len(thai_suspects)} จุด")
        for s in thai_suspects:
            print(f"  - [{s.type}] ตำแหน่ง {s.start}:{s.end} -> {s.text} (เหตุผล: {s.reason})")

if __name__ == "__main__":
    # 1. เปลี่ยนชื่อไฟล์ด้านล่างนี้ให้ตรงกับชื่อไฟล์ PDF ภาษาไทยที่คุณมี
    sample_pdf = "tmp_uploads/sample.pdf"
    
    # 2. เรียกฟังก์ชันทดสอบ
    test_read_with_pdfium(sample_pdf)