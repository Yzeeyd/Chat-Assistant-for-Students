"""
Deterministic parser for Arabic university schedule data.
The AI extracts raw Arabic text from images; this module does all conversion.
"""
from __future__ import annotations

import re
from datetime import datetime, time

from app.core.config import ROOMS_DIR

# ---------------------------------------------------------------------------
# Day mapping
# ---------------------------------------------------------------------------

_ARABIC_DAY_MAP: dict[str, int] = {
    'الأحد': 1, 'أحد': 1,
    'الاثنين': 2, 'اثنين': 2,
    'الثلاثاء': 3, 'ثلاثاء': 3,
    'الأربعاء': 4, 'أربعاء': 4,
    'الخميس': 5, 'خميس': 5,
    'الجمعة': 6, 'جمعة': 6,
    'السبت': 7, 'سبت': 7,
}


def parse_day(value: str) -> int:
    """Return day_of_week (1=Sunday, 7=Saturday) from Arabic name or digit string."""
    v = value.strip()
    if v.isdigit() and 1 <= int(v) <= 7:
        return int(v)
    result = _ARABIC_DAY_MAP.get(v)
    if result:
        return result
    # Try without the definite article prefix
    for prefix in ('ال', 'أل'):
        if v.startswith(prefix):
            result = _ARABIC_DAY_MAP.get(v[2:])
            if result:
                return result
    raise ValueError(f'Unknown day value: {value!r}')


# ---------------------------------------------------------------------------
# Time conversion
# ---------------------------------------------------------------------------

_TIME_PATTERN = re.compile(r'(\d{1,2})[:\.](\d{2})')

# Arabic AM/PM markers (Unicode code points to avoid encoding issues)
_PM_MARKER = 'م'   # م
_AM_MARKER = 'ص'   # ص

_FLEXIBLE_MARKERS = {'بالاتفاق', 'باتفاق', 'by arrangement', 'tba', 'tbd'}


def parse_time(value: str) -> time | None:
    """
    Convert an Arabic AM/PM time string to a Python time object.
    Returns None for flexible/online sessions ("بالاتفاق" etc.).

    Handles:
      "8:00 ص"  -> time(8, 0)      morning class
      "9:00 م"  -> time(21, 0)     evening class
      "1:00 ص"  -> time(1, 0)      late-night Ramadan session
      "10:00"   -> time(10, 0)     no marker, hour 8-12 kept as-is
      "6:00"    -> time(18, 0)     no marker, hour 1-7 treated as PM
    """
    v = (value or '').strip()
    if v.lower() in _FLEXIBLE_MARKERS or 'اتفاق' in v:
        return None
    is_pm = _PM_MARKER in v
    is_am = _AM_MARKER in v

    match = _TIME_PATTERN.search(v)
    if not match:
        raise ValueError(f'Cannot parse time: {value!r}')

    hours = int(match.group(1))
    minutes = int(match.group(2))

    # Apply AM/PM conversion
    if is_pm and hours != 12:
        hours += 12
    elif is_am and hours == 12:
        hours = 0
    elif not is_pm and not is_am and 1 <= hours <= 7:
        # No marker + hour 1-7: university never runs classes at 1-7 AM,
        # so this is a 12-hour time without a م marker — treat as PM.
        hours += 12

    if not (0 <= hours <= 23 and 0 <= minutes <= 59):
        raise ValueError(
            f'Cannot parse a valid time from: {value!r}'
        )

    return time(hours, minutes)


# ---------------------------------------------------------------------------
# Row parser
# ---------------------------------------------------------------------------

def parse_row(row: dict) -> dict:
    """
    Validate and convert one raw schedule row supplied by the AI.

    Expected input keys (strings, copied verbatim from the image):
        course_code, course_name, day_ar, start_time_ar, end_time_ar,
        room, instructor (optional), credits (optional int/string)

    Returns a clean dict ready for crud.add_schedule_item.
    """
    course_code = (row.get('course_code') or '').strip() or None
    course_name = (row.get('course_name') or '').strip()
    if not course_name:
        raise ValueError('course_name is required')

    start_time_ar = str(row.get('start_time_ar', '')).strip()
    end_time_ar   = str(row.get('end_time_ar',   '')).strip()
    is_flexible   = 'اتفاق' in start_time_ar or 'اتفاق' in end_time_ar

    day_ar_raw = str(row.get('day_ar', '')).strip()
    if day_ar_raw and 'اتفاق' not in day_ar_raw:
        day_of_week: int | None = parse_day(day_ar_raw)
    elif is_flexible:
        day_of_week = None
    else:
        raise ValueError(f'day_ar is required for non-flexible sessions: {day_ar_raw!r}')

    start = parse_time(start_time_ar)
    end   = parse_time(end_time_ar)

    room = (row.get('room') or '').strip()

    instructor = row.get('instructor') or None
    if isinstance(instructor, str):
        instructor = instructor.strip() or None

    raw_credits = row.get('credits')
    credits: int | None = None
    if raw_credits is not None:
        try:
            credits = int(raw_credits)
        except (TypeError, ValueError):
            credits = None

    return {
        'course_code': course_code,
        'course_name': course_name,
        'day_of_week': day_of_week,
        'start_time': start,
        'end_time': end,
        'room_text': room,
        'instructor': instructor,
        'credits': credits,
    }


# ---------------------------------------------------------------------------
# Day / room helpers (formerly app/utils/schedule.py)
# ---------------------------------------------------------------------------

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
    s = s.translate(str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789'))
    s = s.replace('—', '-').upper()
    s = re.sub(r'[^A-Z0-9]+', '-', s).strip('-')
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
