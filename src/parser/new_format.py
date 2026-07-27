"""Parser for new-format daily entries (Jun-Jul 2026).

Format:
    齐涛-周五工作汇报（2026-07-17）
    1）新增：
    {content or empty}
    2）复测：
    {content or empty}
    3）审核/复核：
       功能 #101675 (已解决): 三维翻模_简化翻模_弹框增加"显示设置" -100%；
       功能 #101643 (新建): 钢结构_纵墙墙梁布置图_横向墙梁 -100%；
       BUG #102451 (新建): 电力基础_新建工程_特别慢xxxx -100%；
    4）其他
       1). task description。
       2). task description。

    ========
    考勤记录：
    上班时间：08:30，下班时间：18:44
    中途外出记录：无
"""

import re
from datetime import date

from src.models import DailyEntry
from src.parser.common import (
    parse_header,
    parse_attendance,
    parse_task_items,
    parse_review_items,
)


def parse_new_format(entry_text: str) -> DailyEntry:
    """Parse a single new-format daily entry."""
    header_info = parse_header(entry_text)
    if not header_info:
        raise ValueError(f"Cannot parse header from entry: {entry_text[:100]}...")

    weekday_cn, entry_date = header_info
    sections: dict = {
        "新增": [], "复测": [], "审核/复核": [], "其他": []
    }
    lines = entry_text.split('\n')

    # Section pattern: 1）新增, 2）复测, 3）审核/复核, 4）其他
    # Also matches annotated headers like 1）新增(1条）： or 2）审核/复核(6条)：
    # Only matches known section names (NOT task items like 1）task description）
    SECTION_NAMES = r'(新增|复测|审核/复核|其他)'
    section_pattern = re.compile(r'^\d）' + SECTION_NAMES + r'(?:[（(]\d+条[）)])?\s*[：:]?\s*$')

    current_section = None
    current_section_text = []

    # Skip the header line
    first_header_found = False

    for line in lines:
        stripped = line.strip()

        # Skip the first header match
        if not first_header_found:
            if re.search(r'齐涛-.+?工作汇报[（(]', stripped):
                first_header_found = True
                continue
            continue

        # Check for numbered section headers: 1）新增, 2）复测, 3）审核/复核, 4）其他
        m = section_pattern.match(stripped)
        if m:
            # Save previous section
            if current_section is not None and current_section_text:
                tasks = _parse_section_tasks(current_section, '\n'.join(current_section_text))
                sections[current_section] = tasks

            section_name = m.group(1).rstrip('：:')
            # Map section name
            if '审核' in section_name or '复核' in section_name:
                current_section = "审核/复核"
            elif '新增' in section_name:
                current_section = "新增"
            elif '复测' in section_name:
                current_section = "复测"
            elif '其他' in section_name:
                current_section = "其他"
            current_section_text = []
            continue

        # Stop at ======== separator
        if stripped.startswith('========'):
            if current_section is not None and current_section_text:
                tasks = _parse_section_tasks(current_section, '\n'.join(current_section_text))
                sections[current_section] = tasks
            current_section = None
            continue

        # Collect text for current section
        if current_section is not None:
            current_section_text.append(line)

    # Handle case where entry ends without ========
    if current_section is not None and current_section_text:
        tasks = _parse_section_tasks(current_section, '\n'.join(current_section_text))
        sections[current_section] = tasks

    # Remove empty sections
    sections = {k: v for k, v in sections.items() if v}

    attendance = parse_attendance(entry_text)

    return DailyEntry(
        date=entry_date,
        weekday_cn=weekday_cn,
        sections=sections,
        attendance=attendance,
        format_version="new",
        raw_text=entry_text,
    )


def _parse_section_tasks(section_name: str, text: str) -> list[str]:
    """Parse tasks from a section based on section type."""
    if section_name == "审核/复核":
        return parse_review_items(text)
    else:
        return parse_task_items(text + '\n')
