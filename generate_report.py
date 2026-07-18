#!/usr/bin/env python3
"""Week Report Generator - Generate weekly reports from daily work logs.

Usage:
    python generate_report.py --year 2026 --week 20          # Generate Week 20 draft
    python generate_report.py --year 2026 --week 20 --final  # Generate final (no draft suffix)
    python generate_report.py --year 2026 --all-missing      # Generate all missing weeks
    python generate_report.py --year 2026 --stats            # Show log statistics
"""

import argparse
import sys
from pathlib import Path

from src.parser.daily_log_parser import parse_log_for_year
from src.organizer.week_grouper import group_by_project_week, get_week_group_for_project_week
from src.generator.report_builder import build_report
from src.generator.template_renderer import render_report, save_report
from src.organizer.week_numbering import get_week_date_range, format_date_range
from config import DEFAULT_OUTPUT_DIR


def cmd_generate(args):
    """Generate weekly reports."""
    # Parse the daily log
    log_dir = Path(args.log_dir) if args.log_dir else Path(".")
    print(f"Parsing daily log for {args.year}...")
    try:
        entries = parse_log_for_year(log_dir, args.year)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"  Parsed {len(entries)} daily entries.")

    # Group by week
    all_groups = group_by_project_week(entries)

    # Determine which weeks to generate
    if args.all_missing:
        # Generate all weeks that have entries but no existing report file
        existing_weeks = _find_existing_weeks(args.output_dir)
        target_weeks = sorted(
            w for w in all_groups.keys()
            if w >= 0 and w not in existing_weeks
        )
        if not target_weeks:
            print("No missing weeks found. All weeks already have reports.")
            return
    elif args.week is not None:
        target_weeks = [args.week]
    else:
        # Default: generate the next week after the last existing report
        existing_weeks = _find_existing_weeks(args.output_dir)
        last_existing = max(existing_weeks) if existing_weeks else -1
        target_weeks = [last_existing + 1]
        print(f"Last existing report: Week {last_existing}, generating Week {last_existing + 1}")

    # Generate each target week
    for week_num in target_weeks:
        print(f"\n--- Generating Week {week_num} ---")
        start, end = get_week_date_range(week_num)
        print(f"  Date range: {format_date_range(start, end)}")

        # Get or create WeekGroup
        if week_num in all_groups:
            week_group = all_groups[week_num]
        else:
            week_group = get_week_group_for_project_week(entries, week_num)

        if not week_group.entries:
            print(f"  WARNING: No daily entries found for Week {week_num}!")
            print(f"  Generating empty template...")

        # Build and render report
        report = build_report(week_group)
        rendered = render_report(report)

        # Save
        output_path = save_report(
            report,
            output_dir=args.output_dir,
            draft=not args.final,
        )
        print(f"  Report saved to: {output_path}")

        if not args.final:
            print(f"  (Draft mode - review and rename to remove '_草稿' suffix)")

        # Print preview in dry-run mode
        if args.dry_run:
            print("\n" + "=" * 60)
            print(rendered)
            print("=" * 60)

    print(f"\nDone! Generated {len(target_weeks)} report(s).")


def cmd_stats(args):
    """Show statistics about the daily log."""
    log_dir = Path(args.log_dir) if args.log_dir else Path(".")
    print(f"Parsing daily log for {args.year}...")
    try:
        entries = parse_log_for_year(log_dir, args.year)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\n=== Daily Log Statistics ({args.year}) ===")
    print(f"  Total entries: {len(entries)}")
    print(f"  Date range: {entries[0].date} ~ {entries[-1].date}")

    old = sum(1 for e in entries if e.format_version == "old")
    new = sum(1 for e in entries if e.format_version == "new")
    print(f"  Format: {old} old, {new} new")

    # Week stats
    groups = group_by_project_week(entries)
    existing_weeks = _find_existing_weeks(args.output_dir)
    missing_weeks = sorted(
        w for w in groups.keys()
        if w >= 0 and w not in existing_weeks
    )

    print(f"\n  Weeks with entries: {len(groups)}")
    print(f"  Project week range: {min(groups.keys())} ~ {max(groups.keys())}")
    print(f"  Existing reports: {sorted(existing_weeks)}")
    if missing_weeks:
        print(f"  Missing reports for weeks: {missing_weeks}")
    else:
        print(f"  All weeks have reports!")

    # Per-week details
    print(f"\n  Per-week details:")
    for week_num in sorted(groups.keys()):
        wg = groups[week_num]
        has_report = week_num in existing_weeks
        status = "✓" if has_report else "✗"
        dr = format_date_range(wg.start_date, wg.end_date)
        print(f"    Week {week_num:3d}: {dr}  |  {len(wg.entries):2d} days  [{status}]")


def _find_existing_weeks(output_dir: str) -> set:
    """Find project weeks that already have report files."""
    import re
    existing = set()
    output_path = Path(output_dir)
    if not output_path.exists():
        return existing

    pattern = re.compile(r'第(-?\d+)周')
    # Also check reference directory (齐涛/)
    for search_dir in [output_path, Path("齐涛")]:
        if not search_dir.exists():
            continue
        for f in search_dir.iterdir():
            if f.is_file():
                m = pattern.search(f.name)
                if m:
                    try:
                        existing.add(int(m.group(1)))
                    except ValueError:
                        pass

    return existing


def main():
    parser = argparse.ArgumentParser(
        description="Week Report Generator - Generate weekly reports from daily work logs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_report.py --year 2026 --week 20        Generate Week 20 draft
  python generate_report.py --year 2026 --week 20 --final Generate final version
  python generate_report.py --year 2026 --all-missing     Generate all missing weeks
  python generate_report.py --year 2026 --stats           Show log statistics
  python generate_report.py --year 2026                   Auto-detect next week
        """,
    )

    parser.add_argument("--year", type=int, required=True, help="Year to process (e.g., 2026)")
    parser.add_argument("--log-dir", type=str, default=".", help="Directory containing log files")
    parser.add_argument("--output-dir", type=str, default=DEFAULT_OUTPUT_DIR,
                        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})")

    # Action group
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--stats", action="store_true", help="Show statistics only")
    action.add_argument("--week", type=int, help="Generate specific week number")
    action.add_argument("--all-missing", action="store_true",
                        help="Generate all weeks without existing reports")

    parser.add_argument("--final", action="store_true",
                        help="Generate final version (no '_草稿' suffix)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print report to console without saving")

    args = parser.parse_args()

    if args.stats:
        cmd_stats(args)
    else:
        cmd_generate(args)


if __name__ == "__main__":
    main()
