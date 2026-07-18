"""Project week ↔ ISO week numbering and date range calculations.

Project Week 0 starts on the Monday of ISO week 9, 2026 (Feb 23, 2026).
Week 00 = 2026.02.26~03.01 (Thu-Sun partial week).
Weeks before that get negative project week numbers.
"""

from datetime import date, timedelta
from typing import Tuple

from config import WEEK_ZERO_ISO_YEAR, WEEK_ZERO_ISO_WEEK


def iso_week_to_project_week(iso_year: int, iso_week: int) -> int:
    """Convert an ISO week (year, week_number) to a project week number.

    Project week N = ISO week - WEEK_ZERO_ISO_WEEK (for weeks in WEEK_ZERO_ISO_YEAR).
    Weeks before Week 0 get negative numbers.
    """
    # Calculate the offset in weeks from the zero point
    # First, calculate how many weeks from ISO week 1 of WEEK_ZERO_ISO_YEAR
    if iso_year == WEEK_ZERO_ISO_YEAR:
        return iso_week - WEEK_ZERO_ISO_WEEK
    elif iso_year < WEEK_ZERO_ISO_YEAR:
        # Earlier year: negative offset
        # ISO year Y has either 52 or 53 weeks
        weeks_in_year = date(iso_year, 12, 28).isocalendar()[1]
        offset = iso_week - weeks_in_year
        # Recurse to handle year boundaries
        return offset - (WEEK_ZERO_ISO_WEEK - 1)
    else:
        # Later year: positive offset
        weeks_before = date(iso_year - 1, 12, 28).isocalendar()[1]
        return (weeks_before - WEEK_ZERO_ISO_WEEK + 1) + iso_week - 1


def project_week_to_iso_week(project_week: int) -> Tuple[int, int]:
    """Convert a project week number to ISO week (year, week_number)."""
    iso_week = WEEK_ZERO_ISO_WEEK + project_week
    iso_year = WEEK_ZERO_ISO_YEAR

    # Handle year boundaries
    weeks_in_year = date(iso_year, 12, 28).isocalendar()[1]
    while iso_week < 1:
        iso_year -= 1
        iso_week += date(iso_year, 12, 28).isocalendar()[1]
    while iso_week > weeks_in_year:
        iso_week -= weeks_in_year
        iso_year += 1
        weeks_in_year = date(iso_year, 12, 28).isocalendar()[1]

    return (iso_year, iso_week)


def get_week_date_range(project_week: int) -> Tuple[date, date]:
    """Get the (Monday, Sunday) date range for a project week."""
    iso_year, iso_week = project_week_to_iso_week(project_week)
    # ISO week 1 is the week containing Jan 4
    jan4 = date(iso_year, 1, 4)
    # Monday of ISO week 1
    monday_of_week1 = jan4 - timedelta(days=jan4.weekday())
    # Monday of target week
    monday = monday_of_week1 + timedelta(weeks=iso_week - 1)
    sunday = monday + timedelta(days=6)
    return (monday, sunday)


def format_date_range(start: date, end: date) -> str:
    """Format date range as 'YYYY.MM.DD~YYYY.MM.DD'."""
    return f"{start.strftime('%Y.%m.%d')}~{end.strftime('%Y.%m.%d')}"


def get_weekday_iso(entry_date: date) -> int:
    """Get ISO weekday (1=Mon..7=Sun) for a date."""
    return entry_date.isocalendar()[2]
