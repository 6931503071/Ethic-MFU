"""ทดสอบ FilledForm: python test_filled_form.py (รันในโฟลเดอร์ backend/)"""
from pathlib import Path

from app.filled_form import FilledForm, ValueStatus
from app.form_fields import load_template

t = load_template(Path(__file__).resolve().parent.parent / "templates" / "ap02.json")
form = FilledForm.blank(t, "th")

# 1) ฟอร์มเปล่า: ทุกช่องเป็นสีแดง
assert all(v.is_red for v in form.values.values())
print("ฟอร์มเปล่า:", form.progress())

# 2) AI เติมช่องของ AI ได้
form.set_found("title_th", "ผลของการออกกำลังกายต่อความดันโลหิต", source_blocks=(3,))
assert form.values["title_th"].status == ValueStatus.FOUND
assert not form.values["title_th"].is_red

# 3) AI ห้ามเติมช่องของผู้ใช้ (กติกาสำคัญ)
try:
    form.set_found("pi_name", "ผศ.ดร.สมชาย ใจดี")
except PermissionError as e:
    print("OK ระบบถูกห้าม:", e)
else:
    raise AssertionError("AI ต้องเติมช่อง user ไม่ได้")
assert form.values["pi_name"].status == ValueStatus.USER_REQUIRED

# 4) ผู้ใช้กรอกเองได้ และล้างค่าแล้วกลับเป็นสีแดง
form.set_by_user("pi_name", "ผศ.ดร.สมชาย ใจดี")
assert form.values["pi_name"].status == ValueStatus.USER_FILLED
form.set_by_user("pi_name", "   ")
assert form.values["pi_name"].status == ValueStatus.USER_REQUIRED

# 5) รูปแบบค่าผิดชนิดต้อง raise
for fid, bad in (("title_th", ["ไม่ใช่สตริง"]), ("special_a_applies", "yes"), ("recruitment", {"selected": [99]})):
    try:
        form.set_by_user(fid, bad)
    except ValueError:
        pass
    else:
        raise AssertionError(f"{fid} ควร raise")

# 6) gate: ตอบ "ไม่ใช่" -> ทั้งหมวดถูกตัดออกจากรายการสีแดง
before = len(form.red_fields())
form.set_by_user("special_a_applies", False)
assert form.values["special_a_applies"].value is False          # False ไม่ใช่ค่าว่าง
assert form.values["special_a_applies"].status == ValueStatus.USER_FILLED
assert not form.is_section_active("special_a")
after = len(form.red_fields())
assert after < before, (before, after)
print(f"ตัดหมวด A ออก: ช่องแดง {before} -> {after}")

# 7) แปลงไป-กลับ dict (จำลองหน้าเว็บส่งกลับมา) แล้วค่าต้องเหมือนเดิม
form.set_by_user("recruitment", {"selected": [0, 2], "details": {"0": "แจกใบปลิว"}})
form.set_by_user("herb_1", 0)   # radio ตัวเลือกแรก (ค่า 0 ต้องไม่ถูกมองเป็นว่าง)
assert form.values["herb_1"].status == ValueStatus.USER_FILLED
d = form.to_dict()
form2 = FilledForm.from_dict(t, d)
assert form2.to_dict() == d
print("แปลง to_dict/from_dict ไป-กลับ ตรงกัน")

# 8) ไม่เชื่อข้อมูลจากหน้าเว็บ: ถ้าส่งมาว่า pi_name เป็น FOUND (AI เติม) ต้องถูกปฏิเสธ
d["values"]["pi_name"] = {"status": "found", "value": "ปลอม", "source_blocks": []}
try:
    FilledForm.from_dict(t, d)
except PermissionError:
    print("OK from_dict ปฏิเสธ FOUND ในช่องของผู้ใช้")
else:
    raise AssertionError("ต้องปฏิเสธ")

print("\nสรุป:", form.progress())
print("ผ่านทั้งหมด")