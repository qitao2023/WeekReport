"""Render a WeeklyReport to text using the standard template format."""

from pathlib import Path
from typing import Optional

from src.models import WeeklyReport, DayBlock
from config import (
    PERSON_NAME,
    PROJECT_NAME,
    PROFESSIONAL_GROUP,
    SUB_PROJECT,
    PROJECT_GROUP,
    REPORT_FILENAME_DRAFT,
    REPORT_FILENAME_FINAL,
    DEFAULT_OUTPUT_DIR,
)
from src.organizer.week_numbering import format_date_range


def render_report(report: WeeklyReport) -> str:
    """Render a WeeklyReport to a formatted text string.

    Matches the existing weekly report template format.
    """
    lines = []

    # Blank line at start (matching existing format)
    lines.append("")

    # Section 1: 待跟踪问题
    lines.append("一、待跟踪问题")
    lines.append("")

    # Section 2: 上周已完成工作
    lines.append("二、各项目组上周已经完成工作")
    lines.append("    ----------------------------------------------------------------------")
    project_header = f"    <{PROJECT_NAME} 上周已经完成工作>-<完成度>-<负责人>"
    lines.append(project_header)
    lines.append(f"    A、{PROFESSIONAL_GROUP}---------------")

    # Day range for header
    day_range = _compute_day_range(report.completed_day_blocks)
    lines.append(f"      {PERSON_NAME}，{report.total_days}天（{day_range}）")

    # Day blocks
    for block in report.completed_day_blocks:
        lines.append(_render_day_block(block))

    # Section 3: 本周预计完成工作
    lines.append("    --------------------------------------------------------------------------")
    future_header = f"    <{PROJECT_NAME} 本周预计完成工作>-<计算时长><负责人>"
    lines.append(future_header)
    lines.append(f"    A、{PROFESSIONAL_GROUP}---------------")

    # Planned items header
    lines.append(f"      {PERSON_NAME}，{report.planned_days}天（{report.planned_range}）")

    # Planned items — align "天" to same column (63) as day blocks
    if report.planned_items:
        target_col = 63
        for i, (desc, allocation) in enumerate(report.planned_items, start=1):
            prefix_w = _display_width(f"      {i}、")
            desc_w = _display_width(desc)
            alloc_prefix_w = _display_width(allocation.replace('天', ''))
            padding = ' ' * (target_col - prefix_w - desc_w - alloc_prefix_w)
            lines.append(f"      {i}、{desc}{padding}{allocation}（{report.planned_range}）")

    # Section 4: 跨周工作
    lines.append("")
    lines.append(f"四、项目跨周工作。<计算时长><负责人>")
    lines.append("    --------------------------------------------------------------------------")
    lines.append("     <跨周工作完成截止日期>")

    return "\n".join(lines)


def _compute_day_range(blocks: list) -> str:
    """Compute the compact day range string like '周1-5,7'."""
    if not blocks:
        return "周1-5, "

    weekdays = []
    for b in blocks:
        try:
            num = int(b.weekday_cn) if b.weekday_cn.isdigit() else _cn_to_num(b.weekday_cn)
            weekdays.append(num)
        except (ValueError, KeyError):
            continue

    if not weekdays:
        return "周1-5, "

    weekdays = sorted(set(weekdays))

    # Build compact ranges
    ranges = []
    start = weekdays[0]
    end = weekdays[0]

    for w in weekdays[1:]:
        if w == end + 1:
            end = w
        else:
            ranges.append((start, end))
            start = w
            end = w
    ranges.append((start, end))

    parts = []
    for s, e in ranges:
        if s == e:
            parts.append(str(s))
        else:
            parts.append(f"{s}-{e}")

    result = "周" + ",".join(parts)
    # Single range → trailing comma (match existing format: 周1-5, )
    if len(parts) == 1 and '-' in parts[0]:
        result += ", "
    return result


def _cn_to_num(cn: str) -> int:
    """Convert Chinese weekday char to number (1=Mon..7=Sun)."""
    mapping = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "日": 7}
    return mapping.get(cn, 0)


def _display_width(s: str) -> int:
    """Calculate display width using Unicode East Asian Width.
    'W' (Wide) and 'F' (Fullwidth) chars = 2 columns, others = 1.
    """
    import unicodedata
    w = 0
    for ch in s:
        ea = unicodedata.east_asian_width(ch)
        if ea in ('W', 'F'):
            w += 2
        else:
            w += 1
    return w


def _render_day_block(block: DayBlock) -> str:
    """Render a single day block."""
    lines = []

    # Main line with "天" aligned to column 63
    prefix = f"      {block.day_index}、{SUB_PROJECT}："
    prefix_w = _display_width(prefix)
    alloc_prefix_w = _display_width(block.allocation.replace('天', ''))  # "1.0"
    padding = ' ' * (63 - prefix_w - alloc_prefix_w)
    main_line = f"{prefix}{padding}{block.allocation}（{block.weekday_range}, ）,     {block.completion}"
    lines.append(main_line)

    # Task sub-items
    for i, task in enumerate(block.tasks):
        # Last task ends with "。", others with "，"
        if i == len(block.tasks) - 1:
            lines.append(f"         {i+1}). {task}。")
        else:
            lines.append(f"         {i+1}). {task}，")

    return "\n".join(lines)


def save_report(
    report: WeeklyReport,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    draft: bool = True,
) -> Path:
    """Save a rendered report to a file.

    Args:
        report: The WeeklyReport to save.
        output_dir: Directory to save the report in.
        draft: If True, append '_草稿' to filename.

    Returns:
        Path to the saved file.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    date_range_str = format_date_range(report.date_range[0], report.date_range[1])

    if draft:
        filename = REPORT_FILENAME_DRAFT.format(
            week=report.week_number,
            start=date_range_str.split("~")[0],
            end=date_range_str.split("~")[1],
        )
    else:
        filename = REPORT_FILENAME_FINAL.format(
            week=report.week_number,
            start=date_range_str.split("~")[0],
            end=date_range_str.split("~")[1],
        )

    filepath = output_path / filename
    content = render_report(report)
    filepath.write_text(content, encoding='utf-8')

    return filepath
