"""Build a WeeklyReport data model from a WeekGroup."""

from typing import List

from src.models import DailyEntry, WeekGroup, DayBlock, WeeklyReport
from config import (
    PERSON_NAME,
    DEFAULT_DAILY_ALLOCATION,
    DEFAULT_COMPLETION,
    WEEKDAY_CN,
)


def build_report(week_group: WeekGroup, schedule_days: int = 5) -> WeeklyReport:
    """Build a WeeklyReport from a WeekGroup.

    Converts daily entries into DayBlocks with tasks extracted from sections.
    """
    day_blocks: List[DayBlock] = []

    for idx, entry in enumerate(week_group.entries, start=1):
        # Collect all tasks from this day's entry
        tasks = _collect_tasks(entry)

        if not tasks:
            continue

        # Create the weekday range string (e.g., "周1-1", "周5-5")
        iso_weekday = entry.date.isocalendar()[2]  # 1=Mon..7=Sun
        weekday_num = str(iso_weekday)  # "1".."7"
        weekday_range = f"周{weekday_num}-{weekday_num}"

        day_block = DayBlock(
            day_index=idx,
            weekday_cn=weekday_num,
            weekday_range=weekday_range,
            tasks=tasks,
            allocation=DEFAULT_DAILY_ALLOCATION,
            completion=DEFAULT_COMPLETION,
        )
        day_blocks.append(day_block)

    # Build the day range string for the header
    total_days = len(day_blocks)
    if total_days == 0:
        total_days = len(week_group.working_days)

    # Planned items based on schedule
    if schedule_days == 5:
        range_str = "周1-5, "
        planned_items = [
            ("周二晚上文档评审和周四晚上技术支持例会", "0.5天"),
            ("TSSDPro三维翻模相关工作", "4.0天"),
            ("厂房相关工作", "0.5天"),
        ]
    else:
        range_str = "周1-5,7"
        planned_items = [
            ("周二晚上文档评审和周四晚上技术支持例会", "0.5天"),
            ("TSSDPro三维翻模相关工作", "5.0天"),
            ("厂房相关工作", "0.5天"),
        ]

    return WeeklyReport(
        week_number=week_group.project_week_number,
        date_range=(week_group.start_date, week_group.end_date),
        completed_day_blocks=day_blocks,
        total_days=total_days,
        planned_items=planned_items,
        planned_days=schedule_days,
        planned_range=range_str,
        tracking_issues=[],
        cross_week_items=[],
    )


def _collect_tasks(entry: DailyEntry) -> List[str]:
    """Collect and flatten all tasks from a daily entry's sections.

    For new format: 审核/复核 items are summarized; others listed individually.
    For old format: 其他 then bug, listed individually.
    """
    tasks = []

    if entry.format_version == "new":
        # 审核/复核: group by module and summarize
        review = entry.sections.get("审核/复核", [])
        if review:
            groups = {}
            for t in review:
                mod = t.split('_')[0] if '_' in t else '其他'
                groups[mod] = groups.get(mod, 0) + 1
            parts = [f"{mod}{cnt}项" for mod, cnt in groups.items()]
            tasks.append(f"审核{'、'.join(parts)}功能需求")
        # Other sections: list individually
        for section in ["新增", "复测", "其他"]:
            if section in entry.sections:
                tasks.extend(entry.sections[section])
    else:
        if "其他" in entry.sections:
            tasks.extend(entry.sections["其他"])
        if "bug" in entry.sections:
            tasks.extend(entry.sections["bug"])

    # Clean up tasks: strip whitespace and normalize
    cleaned = []
    for t in tasks:
        t = t.strip()
        if t and t not in cleaned:
            cleaned.append(t)

    return cleaned
