from app.suspects import check_text

samples = [
    "โครงการวิจัยนี้ศึกษาผลของการออกกำลังกาย",   # ควรไม่พบ
    "เเพทย์ศาสตร์",                              # THAI_DOUBLE_LEADING_VOWEL -> แ
    "น้ํา",                                      # THAI_DECOMPOSED_SARA_AM -> ำ
    "This is the the study",                     # REPEATED_WORD
    "ชื่อ ........ นามสกุล [PLEASE ENTER DATE]",  # MISSING_FIELD x2
    "ĀîšćǰǰÝćÖǰ",                                # ENCODING_GARBLE
    "1) ชื่อ 2) นามสกุล",                         # ไม่พบ (เลขข้อ ไม่ใช่วงเล็บผิด)
]

for t in samples:
    print(repr(t))
    result = check_text(t)
    if not result:
        print("   (ไม่พบจุดสงสัย)")
    for s in result:
        print(f"   {s.severity:6} {s.type:26} [{s.start}:{s.end}] {s.text!r} -> {s.suggestion!r}")