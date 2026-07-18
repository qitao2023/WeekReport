"""Shared parsing utilities for daily work log entries."""

import re
from datetime import date
from typing import Optional, List, Tuple


# Header pattern: 齐涛-周一工作汇报（2026-01-04）
HEADER_PATTERN = re.compile(
    r'齐涛-(.+?)工作汇报[（(](\d{4}-\d{2}-\d{2})[）)]'
)

# Task item patterns - handles both 1). and 1） numbering styles
OLD_TASK_PATTERN = re.compile(r'(\d+)[\)）][.．。]?\s*(.+?)\s*$')
NEW_TASK_PATTERN = re.compile(r'(\d+)[\)）][.．。]?\s*(.+?)\s*$')

# Review item pattern: 功能 #12345 (状态): 描述 -100%；
REVIEW_ITEM_PATTERN = re.compile(
    r'(?:功能|BUG)\s+#\d+\s*\([^)]*\):\s*(.+?)\s*-\d+%[；;]?\s*$'
)

# Attendance patterns
ATTENDANCE_START = re.compile(r'上班时间[：:]\s*(\d{1,2}:\d{2})')
ATTENDANCE_END = re.compile(r'下班时间[：:]\s*(\d{1,2}:\d{2})')

# New format section markers
NEW_FORMAT_SECTION = re.compile(r'^(\d)）(\S+)\s*[：:]?\s*$')

# Weekday name mapping
WEEKDAY_NAME_MAP = {
    "周日": "日", "星期一": "一", "周二": "二", "周三": "三",
    "周四": "四", "周五": "五", "周六": "六",
    "周一": "一", "周日": "日",
    "星期天": "日", "星期天": "日",
}


def parse_header(text: str) -> Optional[Tuple[str, date]]:
    """Parse entry header, return (weekday_cn, date) or None."""
    m = HEADER_PATTERN.search(text)
    if not m:
        return None
    weekday_raw = m.group(1).strip()
    date_str = m.group(2)
    # Normalize weekday to single Chinese char
    weekday_cn = weekday_raw
    for full, short in WEEKDAY_NAME_MAP.items():
        if full in weekday_raw:
            weekday_cn = short
            break
    try:
        entry_date = date.fromisoformat(date_str)
    except ValueError:
        return None
    return (weekday_cn, entry_date)


def parse_attendance(text: str) -> Optional[Tuple[str, str]]:
    """Extract (上班时间, 下班时间) from attendance footer."""
    start_m = ATTENDANCE_START.search(text)
    end_m = ATTENDANCE_END.search(text)
    if start_m and end_m:
        return (start_m.group(1), end_m.group(1))
    return None


def detect_format(text: str) -> str:
    """Detect whether entry uses old or new format. Returns "old" or "new"."""
    # Check for new format numbered sections (1）新增, 2）复测, etc.)
    lines = text.strip().split('\n')
    for line in lines[:20]:  # Check first 20 lines after header
        stripped = line.strip()
        if re.match(r'^[1-4]\）(?:新增|复测|审核/复核|其他)', stripped):
            return "new"
    return "old"


def parse_task_items(text: str) -> List[str]:
    """Parse numbered task items like '1). task description，' or '1). task description。'"""
    tasks = []
    for line in text.split('\n'):
        stripped = line.strip()
        if not stripped:
            continue
        m = OLD_TASK_PATTERN.match(stripped)
        if m:
            task = m.group(2).strip()
            # Strip trailing Chinese punctuation
            task = re.sub(r'[，,。\.；;、]+$', '', task)
            if task:
                tasks.append(task)
    return tasks


def parse_review_items(text: str) -> List[str]:
    """Parse review items with bug IDs like '功能 #12345 (状态): 描述 -100%；'"""
    tasks = []
    for line in text.split('\n'):
        stripped = line.strip()
        if not stripped:
            continue
        m = REVIEW_ITEM_PATTERN.match(stripped)
        if m:
            task = m.group(1).strip()
            if task:
                tasks.append(task)
    return tasks


def split_into_entries(raw_text: str) -> List[Tuple[str, int, int]]:
    """Split raw log file into individual daily entries.
    Returns list of (entry_text, start_line, end_line) tuples.
    """
    lines = raw_text.split('\n')
    entries = []
    current_start = None
    current_lines = []

    for i, line in enumerate(lines):
        # Detect entry header
        if HEADER_PATTERN.search(line):
            # Save previous entry if any
            if current_start is not None and current_lines:
                entry_text = '\n'.join(current_lines)
                entries.append((entry_text, current_start, current_start + len(current_lines) - 1))
            current_start = i
            current_lines = [line]
        elif current_start is not None:
            current_lines.append(line)

    # Don't forget the last entry
    if current_start is not None and current_lines:
        entry_text = '\n'.join(current_lines)
        entries.append((entry_text, current_start, current_start + len(current_lines) - 1))

    return entries
