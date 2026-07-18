"""Configuration constants for the weekly report generator."""

# Person and project info
PERSON_NAME = "齐涛"
PROJECT_GROUP = "TSSDPro项目组"
PROJECT_NAME = "TSSDPro-MTS-TSSD计算1"
PROFESSIONAL_GROUP = "TSSDPro专业组"
SUB_PROJECT = "TSSDPro、TSMGN"

# Project Week 0 starts on the Monday of ISO week 9, 2026
# Week 00 = 2026.02.26~03.01 (Thu-Sun partial week, monday is Feb 23 = ISO week 9)
WEEK_ZERO_ISO_YEAR = 2026
WEEK_ZERO_ISO_WEEK = 9

# File paths
LOG_FILE_TEMPLATE = "工作日志 -{year}.txt"
DEFAULT_OUTPUT_DIR = "reports"
REFERENCE_DIR = "齐涛"

# Report template
REPORT_FILENAME_DRAFT = "TSSDPro项目组_齐涛_周报_第{week:02d}周({start}~{end})_草稿.txt"
REPORT_FILENAME_FINAL = "TSSDPro项目组_齐涛_周报_第{week:02d}周({start}~{end}).txt"

# Weekday mapping: Python weekday() 0=Mon → Chinese weekday
WEEKDAY_CN = {
    0: "一", 1: "二", 2: "三", 3: "四",
    4: "五", 5: "六", 6: "日",
}

# Format detection markers for new format
NEW_FORMAT_MARKERS = [
    r'新增\s*[：:]',
    r'复测\s*[：:]',
    r'审核/复核\s*[：:]',
    r'^\d+\）新增',
    r'^\d+\）复测',
    r'^\d+\）审核/复核',
]

# Default values for report
DEFAULT_DAILY_ALLOCATION = "1.0天"
DEFAULT_COMPLETION = "100%"
