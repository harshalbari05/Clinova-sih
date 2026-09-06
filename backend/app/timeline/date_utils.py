"""Date parsing and precision normalization for Clinova Step 8: Medical Timeline.

CRITICAL SAFETY PRINCIPLE:
Never fabricate exact dates. If a source only documents a year, a month,
or an approximate period (e.g., 'about five years ago'), the date precision
must strictly reflect that uncertainty.
"""

from __future__ import annotations

import re
from datetime import date, datetime

_MONTH_NAMES = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

_APPROXIMATE_KEYWORDS = (
    "about",
    "around",
    "approx",
    "approximately",
    "years ago",
    "months ago",
    "weeks ago",
    "days ago",
    "since",
    "childhood",
    "past",
    "nearly",
    "roughly",
    "estimated",
)


def parse_clinical_date(raw: str | date | datetime | None) -> tuple[date | None, str]:
    """Parse a clinical date string into a date object and its precision enum value.

    Returns:
        tuple[date | None, str]: (parsed_date, precision)
        precision is one of: "EXACT", "MONTH", "YEAR", "APPROXIMATE", "UNKNOWN"
    """
    if raw is None:
        return None, "UNKNOWN"

    if isinstance(raw, datetime):
        return raw.date(), "EXACT"

    if isinstance(raw, date):
        return raw, "EXACT"

    text = str(raw).strip()
    if not text:
        return None, "UNKNOWN"

    lower_text = text.lower()

    # 1. Check for approximate phrases
    for kw in _APPROXIMATE_KEYWORDS:
        if kw in lower_text:
            # Check if there is an explicit 4-digit year inside the approximate text (e.g., 'approx 2019')
            year_match = re.search(r"\b(19\d\d|20\d\d)\b", text)
            if year_match:
                try:
                    y = int(year_match.group(1))
                    return date(y, 1, 1), "APPROXIMATE"
                except ValueError:
                    pass
            return None, "APPROXIMATE"

    # 2. ISO format: YYYY-MM-DD
    iso_match = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", text)
    if iso_match:
        try:
            return (
                date(
                    int(iso_match.group(1)),
                    int(iso_match.group(2)),
                    int(iso_match.group(3)),
                ),
                "EXACT",
            )
        except ValueError:
            pass

    # 3. DD/MM/YYYY or DD-MM-YYYY or DD.MM.YYYY
    dmy_match = re.match(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})$", text)
    if dmy_match:
        d, m, y = (
            int(dmy_match.group(1)),
            int(dmy_match.group(2)),
            int(dmy_match.group(3)),
        )
        try:
            # Try day/month/year first (standard in Indian/UK medical records)
            return date(y, m, d), "EXACT"
        except ValueError:
            try:
                # Fallback to month/day/year if day > 12 was in month position
                return date(y, d, m), "EXACT"
            except ValueError:
                pass

    # 4. Formats with word months: e.g., '15 March 2025', '15-Mar-2025', 'March 15, 2025'
    named_day_month = re.match(
        r"^(\d{1,2})[\s/-]+([a-zA-Z]+)[\s/-]+(\d{4})$", text
    )
    if named_day_month:
        d_val = int(named_day_month.group(1))
        m_str = named_day_month.group(2).lower()
        y_val = int(named_day_month.group(3))
        m_val = _MONTH_NAMES.get(m_str) or _MONTH_NAMES.get(m_str[:3])
        if m_val:
            try:
                return date(y_val, m_val, d_val), "EXACT"
            except ValueError:
                pass

    month_day_named = re.match(
        r"^([a-zA-Z]+)[\s/-]+(\d{1,2}),?[\s/-]+(\d{4})$", text
    )
    if month_day_named:
        m_str = month_day_named.group(1).lower()
        d_val = int(month_day_named.group(2))
        y_val = int(month_day_named.group(3))
        m_val = _MONTH_NAMES.get(m_str) or _MONTH_NAMES.get(m_str[:3])
        if m_val:
            try:
                return date(y_val, m_val, d_val), "EXACT"
            except ValueError:
                pass

    # 5. Month and Year only: e.g. 'March 2025', 'Mar 2025', '2025-03'
    month_year_iso = re.match(r"^(\d{4})-(\d{1,2})$", text)
    if month_year_iso:
        try:
            return (
                date(int(month_year_iso.group(1)), int(month_year_iso.group(2)), 1),
                "MONTH",
            )
        except ValueError:
            pass

    named_month_year = re.match(r"^([a-zA-Z]+)[\s/-]+(\d{4})$", text)
    if named_month_year:
        m_str = named_month_year.group(1).lower()
        y_val = int(named_month_year.group(2))
        m_val = _MONTH_NAMES.get(m_str) or _MONTH_NAMES.get(m_str[:3])
        if m_val:
            try:
                return date(y_val, m_val, 1), "MONTH"
            except ValueError:
                pass

    # 6. Year only: e.g. '2025'
    year_only = re.match(r"^(\d{4})$", text)
    if year_only:
        y_val = int(year_only.group(1))
        if 1900 <= y_val <= 2100:
            return date(y_val, 1, 1), "YEAR"

    # 7. Unrecognized string
    return None, "UNKNOWN"
