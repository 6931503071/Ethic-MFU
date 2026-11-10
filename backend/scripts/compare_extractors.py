import sys
import pdfplumber
import fitz  # PyMuPDF

path = sys.argv[1]
page_no = int(sys.argv[2]) if len(sys.argv) > 2 else 2

with pdfplumber.open(path) as pdf:
    t1 = pdf.pages[page_no - 1].extract_text() or ""

doc = fitz.open(path)
t2 = doc[page_no - 1].get_text()

KEYWORDS = ["ระบุห้อง", "ระบหุ ้อง", "ทำให้สนใจ", "ทำใหส้ นใจ",
            "เครื่องหมาย", "เครอื่งหมาย"]

for name, t in [("pdfplumber", t1), ("pymupdf", t2)]:
    print(f"\n=== {name} ===")
    for kw in KEYWORDS:
        print(f"{kw!r}: {'พบ' if kw in t else '-'}")
    print(f"--- 300 ตัวอักษรแรก ---\n{t[:300]}")