"""
Deterministic parser for Arabic university schedule data.
The AI extracts raw Arabic text from images; this module does all conversion.
"""
from __future__ import annotations

import re
from datetime import time

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


def parse_time(value: str) -> time:
    """
    Convert an Arabic AM/PM time string to a Python time object.

    Handles:
      "8:00 ص"  -> time(8, 0)      morning class
      "9:50 ص"  -> time(9, 50)
      "1:00 م"  -> time(13, 0)     afternoon class
      "12:00 م" -> time(12, 0)     noon
      "10:00"   -> time(10, 0)     no marker, treat as 24h

    Auto-correction:
      University classes run 06:00-17:00 only.
      If the converted hour is > 17 (e.g. "9:00 م" → 21:00), the AI misread
      ص as م. We subtract 12 to recover the correct morning time.
    """
    v = (value or '').strip()
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
    # No marker: assume value is already in 24-hour format

    # Auto-correct AI misread: if result > 17:00, the marker was probably wrong.
    # Subtracting 12 recovers the correct morning hour (e.g. 21 -> 9).
    if hours > 17:
        corrected = hours - 12
        if 6 <= corrected <= 17:
            hours = corrected

    if not (6 <= hours <= 17 and 0 <= minutes <= 59):
        raise ValueError(
            f'Time {hours:02d}:{minutes:02d} is outside university class hours (06:00-17:00). '
            f'Original: {value!r}'
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

    day_of_week = parse_day(str(row.get('day_ar', '')))
    start = parse_time(str(row.get('start_time_ar', '')))
    end = parse_time(str(row.get('end_time_ar', '')))

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
