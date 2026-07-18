"""Top-level daily log parser that orchestrates format detection and parsing."""

import re
from pathlib import Path
from typing import Union, List

from src.models import DailyEntry
from src.parser.common import (
    split_into_entries,
    parse_header,
    detect_format,
)
from src.parser.old_format import parse_old_format
from src.parser.new_format import parse_new_format


def parse_log(filepath: Union[str, Path]) -> List[DailyEntry]:
    """Parse a daily work log file and return all entries.

    Args:
        filepath: Path to the log file (e.g., '工作日志 -2026.txt')

    Returns:
        List of DailyEntry objects, sorted by date.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Log file not found: {filepath}")

    raw_text = filepath.read_text(encoding='utf-8')

    # Split into individual entry blocks
    entry_blocks = split_into_entries(raw_text)
    if not entry_blocks:
        raise ValueError(f"No valid daily entries found in {filepath}")

    entries: List[DailyEntry] = []
    skipped = 0

    for entry_text, start_line, end_line in entry_blocks:
        # Verify this is a valid entry
        header_info = parse_header(entry_text)
        if not header_info:
            skipped += 1
            continue

        # Detect format and parse
        fmt = detect_format(entry_text)
        try:
            if fmt == "new":
                entry = parse_new_format(entry_text)
            else:
                entry = parse_old_format(entry_text)
            entries.append(entry)
        except Exception as e:
            print(f"Warning: Skipping entry at lines {start_line+1}-{end_line+1}: {e}")
            skipped += 1

    # Sort by date
    entries.sort(key=lambda e: e.date)

    if skipped > 0:
        print(f"Parsed {len(entries)} entries, skipped {skipped} unparseable blocks.")

    return entries


def parse_log_for_year(log_dir: Union[str, Path], year: int) -> List[DailyEntry]:
    """Parse the log file for a specific year.

    Args:
        log_dir: Directory containing the log file
        year: Year to parse (e.g., 2026)

    Returns:
        List of DailyEntry objects.
    """
    from config import LOG_FILE_TEMPLATE

    log_dir = Path(log_dir)
    filename = LOG_FILE_TEMPLATE.format(year=year)
    filepath = log_dir / filename

    if not filepath.exists():
        # Try current directory
        filepath = Path(filename)
        if not filepath.exists():
            raise FileNotFoundError(
                f"Log file not found: {log_dir / filename} or ./{filename}"
            )

    return parse_log(filepath)
