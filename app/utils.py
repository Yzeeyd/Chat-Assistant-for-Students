import re
from datetime import datetime
import os

def today_dow_1_to_7() -> int:
    return ((datetime.now().weekday() + 1) % 7) + 1

def normalize_room_text(room_text: str) -> str:
    if not room_text:
        return ""

    room_text = room_text.strip()
    room_text = room_text.translate(str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789"))

    # إزالة الفراغات وتوحيد الشرطة
    room_text = room_text.replace("—", "-")
    room_text = re.sub(r"\s+", "", room_text)

    # الإبقاء فقط على الأرقام والشرطة
    room_text = re.sub(r"[^0-9\-]", "", room_text)

    parts = room_text.split("-")
    if len(parts) == 3:
        a, b, c = parts

        # إذا كانت مقلوبة مثل 16-1-046 -> 046-1-16
        if len(a) <= 2 and len(c) == 3:
            room_text = f"{c}-{b}-{a}"

    return room_text
#دالة ايجاد الصور
def find_room_image(room_text: str) -> str | None:
    UPLOADS_DIR = os.path.join(os.getcwd(), "uploads")
    ROOMS_DIR = os.path.join(UPLOADS_DIR, "rooms")

    room_text = normalize_room_text(room_text)
    for ext in (".png", ".jpg", ".jpeg"):
        filename = f"{room_text}{ext}"
        path = os.path.join(ROOMS_DIR, filename)
        if os.path.exists(path):
            return f"/static/rooms/{filename}"
    return None
