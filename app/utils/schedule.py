import os
import re
from datetime import datetime

from app.core.config import ROOMS_DIR


def today_dow_1_to_7() -> int:
    return ((datetime.now().weekday() + 1) % 7) + 1


def normalize_room_text(room_text: str) -> str:
    if not room_text:
        return ''
    room_text = room_text.strip()
    if room_text.lower() == 'online' or room_text == 'اونلاين':
        return room_text
    room_text = room_text.translate(str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789'))
    room_text = room_text.replace('—', '-')
    room_text = re.sub(r'\s+', '', room_text)
    room_text = re.sub(r'[^0-9\-]', '', room_text)
    parts = room_text.split('-')
    if len(parts) == 3:
        a, b, c = parts
        if len(a) <= 2 and len(c) == 3:
            room_text = f'{c}-{b}-{a}'
    return room_text


def find_room_image(room_text: str) -> str | None:
    normalized = normalize_room_text(room_text)
    for ext in ('.png', '.jpg', '.jpeg', '.webp'):
        filename = f'{normalized}{ext}'
        path = ROOMS_DIR / filename
        if path.exists():
            return f'/static/rooms/{filename}'
    return None
