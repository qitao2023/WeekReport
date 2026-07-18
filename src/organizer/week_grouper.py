"""Group daily entries by project week."""

from collections import defaultdict
from datetime import date
from typing import List, Dict

from src.models import DailyEntry, WeekGroup
from src.organizer.week_numbering import (
    iso_week_to_project_week,
    get_week_date_range,
    get_weekday_iso,
)


def group_by_project_week(entries: List[DailyEntry]) -> Dict[int, WeekGroup]:
    """Group daily entries by project week.

    Args:
        entries: List of DailyEntry objects sorted by date.

    Returns:
        Dict mapping project_week_number → WeekGroup.
    """
    # Group entries by ISO week
    iso_groups: Dict[tuple, List[DailyEntry]] = defaultdict(list)
    for entry in entries:
        iso_year, iso_week, _ = entry.date.isocalendar()
        iso_groups[(iso_year, iso_week)].append(entry)

    # Convert to project week groups
    week_groups: Dict[int, WeekGroup] = {}
    for (iso_year, iso_week), group_entries in iso_groups.items():
        project_week = iso_week_to_project_week(iso_year, iso_week)
        start_date, end_date = get_week_date_range(project_week)
        working_days = sorted(set(
            get_weekday_iso(e.date) for e in group_entries
        ))

        week_groups[project_week] = WeekGroup(
            project_week_number=project_week,
            iso_week=(iso_year, iso_week),
            start_date=start_date,
            end_date=end_date,
            entries=sorted(group_entries, key=lambda e: e.date),
            working_days=working_days,
        )

    return week_groups


def get_week_group_for_project_week(
    entries: List[DailyEntry],
    project_week: int,
) -> WeekGroup:
    """Get the WeekGroup for a specific project week.

    If the week has no entries, returns an empty WeekGroup with just date info.
    """
    start_date, end_date = get_week_date_range(project_week)

    # Filter entries that fall within this week's date range
    week_entries = [
        e for e in entries
        if start_date <= e.date <= end_date
    ]

    working_days = sorted(set(
        get_weekday_iso(e.date) for e in week_entries
    ))

    return WeekGroup(
        project_week_number=project_week,
        iso_week=(start_date.isocalendar()[0], start_date.isocalendar()[1]),
        start_date=start_date,
        end_date=end_date,
        entries=sorted(week_entries, key=lambda e: e.date),
        working_days=working_days,
    )
