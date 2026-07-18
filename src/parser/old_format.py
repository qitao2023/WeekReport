"""Parser for old-format daily entries (Jan-May 2026).

Format:
    齐涛-周日工作汇报（2026-01-04）
    bug：
    {bug items or empty}

    其他：
    1). task description。
    2). task description。

    ========
    考勤记录：：：
    上班时间：08:30，下班时间：18:17
"""

import re
from datetime import date

from src.models import DailyEntry
from src.parser.common import (
    parse_header,
    parse_attendance,
    parse_task_items,
)

# Section header patterns for old format
BUG_HEADER = re.compile(r'^bug[：:]\s*$')
OTHER_HEADER = re.compile(r'^其他[：:]\s*$')


def parse_old_format(entry_text: str) -> DailyEntry:
    """Parse a single old-format daily entry."""
    header_info = parse_header(entry_text)
    if not header_info:
        raise ValueError(f"Cannot parse header from entry: {entry_text[:100]}...")

    weekday_cn, entry_date = header_info
    sections: dict = {"bug": [], "其他": []}
    lines = entry_text.split('\n')

    # Parse sections
    current_section = None
    current_section_text: list[str] = []

    for line in lines:
        stripped = line.strip()

        # Check for bug header
        if BUG_HEADER.match(stripped):
            if current_section is not None and current_section_text:
                tasks = parse_task_items('\n'.join(current_section_text))
                sections[current_section] = tasks
            current_section = "bug"
            current_section_text = []
            continue

        # Check for 其他 header
        if OTHER_HEADER.match(stripped):
            if current_section is not None and current_section_text:
                tasks = parse_task_items('\n'.join(current_section_text))
                sections[current_section] = tasks
            current_section = "其他"
            current_section_text = []
            continue

        # Stop at ======== separator (attendance follows)
        if stripped.startswith('========'):
            if current_section is not None and current_section_text:
                tasks = parse_task_items('\n'.join(current_section_text))
                sections[current_section] = tasks
            current_section = None
            continue

        # Collect text for current section
        if current_section is not None:
            current_section_text.append(line)

    # Handle case where entry ends without ========
    if current_section is not None and current_section_text:
        tasks = parse_task_items('\n'.join(current_section_text))
        sections[current_section] = tasks

    # Remove empty sections
    sections = {k: v for k, v in sections.items() if v}

    attendance = parse_attendance(entry_text)

    return DailyEntry(
        date=entry_date,
        weekday_cn=weekday_cn,
        sections=sections,
        attendance=attendance,
        format_version="old",
        raw_text=entry_text,
    )
