"""Data models for the weekly report generator."""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional, List, Dict, Tuple


@dataclass
class DailyEntry:
    """A single day's work log entry."""
    date: date
    weekday_cn: str              # e.g., "一", "日"
    sections: Dict[str, List[str]] = field(default_factory=dict)
    # Old format: {"bug": [...], "其他": [...]}
    # New format: {"新增": [...], "复测": [...], "审核/复核": [...], "其他": [...]}
    attendance: Optional[Tuple[str, str]] = None  # (上班, 下班)
    format_version: str = "old"   # "old" or "new"
    raw_text: str = ""            # original entry text for reference


@dataclass
class WeekGroup:
    """A week's worth of daily entries grouped together."""
    project_week_number: int      # 0-based project week number
    iso_week: Tuple[int, int]     # (year, week_number)
    start_date: date              # Monday of the week
    end_date: date                # Sunday of the week
    entries: List[DailyEntry] = field(default_factory=list)
    working_days: List[int] = field(default_factory=list)  # ISO weekday nums (1=Mon..7=Sun)


@dataclass
class DayBlock:
    """A single day's work rendered as a report block."""
    day_index: int                # 1-based position within the week
    weekday_cn: str               # "一"~"日"
    weekday_range: str            # "周1-1", "周5-5", etc.
    tasks: List[str] = field(default_factory=list)  # Cleaned task descriptions
    allocation: str = "1.0天"
    completion: str = "100%"


@dataclass
class WeeklyReport:
    """Complete weekly report data."""
    week_number: int
    date_range: Tuple[date, date]  # (start, end)
    completed_day_blocks: List[DayBlock] = field(default_factory=list)
    total_days: int = 0
    planned_items: List[Tuple[str, str]] = field(default_factory=list)  # (desc, allocation)
    planned_days: int = 5
    planned_range: str = "周1-5"
    tracking_issues: List[str] = field(default_factory=list)
    cross_week_items: List[str] = field(default_factory=list)
