"""ทดสอบตัวโหลดเทมเพลต: python test_form_fields.py (รันในโฟลเดอร์ backend/)"""
import json
import tempfile
from collections import Counter
from pathlib import Path

from app.form_fields import FieldType, FillBy, TemplateError, load_template

TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "ap02.json"

t = load_template(TEMPLATE)
fields = list(t.iter_fields())
sections = list(t.iter_sections())
print("หมวดทั้งหมด (รวมหมวดย่อย):", len(sections), "| หมวดระดับบนสุด:", len(t.sections))
print("ช่องทั้งหมด (รวม gate + หัวกระดาษ):", len(fields))
print("แยกตาม fill_by:", dict(Counter(f.fill_by.value for f in fields)))
print("แยกตาม type:", dict(Counter(f.type.value for f in fields)))
print("คำเตือนคีย์แปลก:", t.warnings or "ไม่มี")

assert len(t.sections) == 19
assert len({f.id for f in fields}) == len(fields), "id ต้องไม่ซ้ำ"
assert t.get_field("pi_name").fill_by == FillBy.USER
assert t.get_field("title_th").text("en") == "(Thai Title)"
assert t.get_field("special_a_applies").is_gate
assert t.get_field("co_investigators").type == FieldType.TABLE
assert [s.id for s in t.section_chain("pi")][-1] == "team"   # หมวดแม่

# กรณีผิดพลาดต้อง raise
def broken(mutate):
    raw = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    mutate(raw)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False)
    return Path(f.name)

for name, mutate in {
    "type ไม่รู้จัก": lambda r: r["sections"][0]["fields"][0].update(type="banana"),
    "id ซ้ำ": lambda r: r["sections"][0]["fields"][1].update(id="title_th"),
}.items():
    p = broken(mutate)
    try:
        load_template(p)
    except TemplateError as e:
        print(f"OK ตรวจเจอ [{name}]:", str(e).splitlines()[-1][:90])
    else:
        raise AssertionError(f"ควร raise: {name}")
    finally:
        p.unlink(missing_ok=True)

print("\nผ่านทั้งหมด")