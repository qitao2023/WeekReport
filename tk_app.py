#!/usr/bin/env python3
"""周报生成器"""

import re
import sys
import tkinter as tk
from tkinter import messagebox
from pathlib import Path


def _get_data_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent.parent.parent.parent
    return Path(__file__).parent


def _get_source_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


DATA_DIR = _get_data_dir()
sys.path.insert(0, str(_get_source_dir()))

from src.parser.daily_log_parser import parse_log
from src.organizer.week_grouper import group_by_project_week
from src.organizer.week_numbering import format_date_range
from src.generator.report_builder import build_report
from src.generator.template_renderer import render_report

LOG_FILE = DATA_DIR / "工作日志 -2026.txt"
OUT_DIR = DATA_DIR / "齐涛"


def generate():
    if not LOG_FILE.is_file():
        messagebox.showerror("Error", f"Log not found:\n{LOG_FILE}")
        return
    if not OUT_DIR.is_dir():
        messagebox.showerror("Error", f"Output dir not found:\n{OUT_DIR}")
        return

    try:
        status_var.set("Parsing...")
        root.update()

        entries = parse_log(str(LOG_FILE))
        groups = group_by_project_week(entries)

        existing = set()
        for f in OUT_DIR.iterdir():
            if f.is_file() and f.suffix == '.txt':
                m = re.search(r'第(\d+)周', f.name)
                if m:
                    existing.add(int(m.group(1)))

        missing = sorted(w for w in groups if w >= 0 and w not in existing)
        if not missing:
            messagebox.showinfo("Info", "All weeks have reports.")
            status_var.set("Done - no missing weeks")
            return

        week_num = missing[0]
        wg = groups[week_num]
        dr = format_date_range(wg.start_date, wg.end_date)

        status_var.set(f"Generating week {week_num} ({dr})...")
        root.update()

        report = build_report(wg)
        text = render_report(report)

        filename = f"TSSDPro项目组_齐涛_周报_第{week_num:02d}周({wg.start_date.strftime('%Y.%m.%d')}~{wg.end_date.strftime('%Y.%m.%d')}).txt"
        filepath = OUT_DIR / filename
        filepath.write_text(text, encoding='utf-8')

        status_var.set(f"Done: {filename}")
        messagebox.showinfo("Success", f"Week {week_num} saved to:\n{filepath}")

    except Exception as e:
        messagebox.showerror("Error", str(e))
        status_var.set("Failed")


# ── GUI: most basic possible ──
root = tk.Tk()
root.title("ZhouBao Generator")
root.geometry("700x250")

# Use grid layout - explicit rows
row = 0
tk.Label(root, text="=== ZhouBao Generator ===", fg="black").grid(row=row, column=0, sticky="w", padx=20, pady=(20, 10))
row += 1
tk.Label(root, text=f"Log: {LOG_FILE}", fg="black").grid(row=row, column=0, sticky="w", padx=20)
row += 1
tk.Label(root, text=f"Out: {OUT_DIR}", fg="black").grid(row=row, column=0, sticky="w", padx=20)
row += 1
tk.Button(root, text="Generate Report", command=generate, bg="blue", fg="white",
          padx=30, pady=5).grid(row=row, column=0, pady=(20, 10))
row += 1
status_var = tk.StringVar(value="Ready")
tk.Label(root, textvariable=status_var, fg="gray").grid(row=row, column=0, sticky="w", padx=20)

root.mainloop()
