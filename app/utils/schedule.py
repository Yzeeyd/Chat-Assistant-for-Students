import os
import re
from datetime import datetime

from app.core.config import ROOMS_DIR


def today_dow_1_to_7() -> int:
    return ((datetime.now().weekday() + 1) % 7) + 1


def normalize_room_text(room_text: str) -> str:
    """Canonicalize a room label so it maps to a filename under uploads/rooms/.

    Handles two campus formats:
      - "046 - 1 - 18"        →  "046-1-18"        (digits-only, hyphenated)
      - "Z 87 3 G 138"        →  "Z-87-3-G-138"    (zone+letters, space-separated)
      - "18 - 1 - 046"        →  "046-1-18"        (legacy reversed digits)
    """
    if not room_text:
        return ''
    s = room_text.strip()
    if s.lower() == 'online' or s == 'اونلاين':
        return s
    # Arabic-Indic digits → ASCII; em-dash → hyphen; uppercase letters for consistency.
    s = s.translate(str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789'))
    s = s.replace('—', '-').upper()
    # Collapse any run of non-alphanumeric characters into a single hyphen.
    s = re.sub(r'[^A-Z0-9]+', '-', s).strip('-')
    # Legacy swap: pure-digit reversed triplet like "18-1-046" → "046-1-18".
    parts = s.split('-')
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        a, b, c = parts
        if len(a) <= 2 and len(c) == 3:
            s = f'{c}-{b}-{a}'
    return s


def find_room_image(room_text: str) -> str | None:
    normalized = normalize_room_text(room_text)
    for ext in ('.png', '.jpg', '.jpeg', '.webp'):
        filename = f'{normalized}{ext}'
        path = ROOMS_DIR / filename
        if path.exists():
            return f'/static/rooms/{filename}'
    return None
