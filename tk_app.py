#!/usr/bin/env python3
"""周报生成器 - Windows 桌面版"""

import os
import re
import sys
import platform
import json
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox

# ── Appearance ──────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ── Paths ───────────────────────────────────────────────────
def _get_data_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
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


def open_file(path):
    """Cross-platform open file with default app."""
    if platform.system() == 'Windows':
        os.startfile(path)
    elif platform.system() == 'Darwin':
        import subprocess
        subprocess.run(['open', path])
    else:
        import subprocess
        subprocess.run(['xdg-open', path])


# ── Colors (Apple-style) ────────────────────────────────────
BG = "#f5f5f7"
LABEL_GRAY = "#86868b"
BLUE = "#007AFF"
BLUE_HOVER = "#0062cc"
BORDER = "#d1d1d6"
TEXT_DARK = "#1d1d1f"
GREEN = "#34c759"
RED = "#ff3b30"
WHITE = "#ffffff"


class WeekReportApp:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("周报生成器")
        self.window.geometry("520x460")
        self.window.resizable(True, True)
        self.window.configure(fg_color=BG)

        # Fonts
        self.font_title = ctk.CTkFont(family="Microsoft YaHei UI", size=17, weight="bold")
        self.font_label = ctk.CTkFont(family="Microsoft YaHei UI", size=10, weight="bold")
        self.font_entry = ctk.CTkFont(family="Cascadia Code", size=11)
        self.font_btn = ctk.CTkFont(family="Microsoft YaHei UI", size=12, weight="bold")
        self.font_msg = ctk.CTkFont(family="Microsoft YaHei UI", size=12)

        self.schedule_days = 5
        self.week_options = []
        self.week_data = {}  # week_num -> {range, days, done}

        self._build_ui()
        self._load_defaults()

    # ── UI Construction ──────────────────────────────────
    def _build_ui(self):
        pad_x = 28
        pad_y = 6

        # Title
        self.lbl_title = ctk.CTkLabel(
            self.window, text="🗂️  周报生成器",
            font=self.font_title, text_color=TEXT_DARK,
        )
        self.lbl_title.pack(pady=(24, 16), padx=pad_x, anchor="w")

        # ── Log file ──
        self.lbl_log = ctk.CTkLabel(
            self.window, text="日志文件", font=self.font_label,
            text_color=LABEL_GRAY,
        )
        self.lbl_log.pack(padx=pad_x, pady=(0, 2), anchor="w")

        row_log = ctk.CTkFrame(self.window, fg_color="transparent")
        row_log.pack(fill="x", padx=pad_x, pady=(0, pad_y))
        self.entry_log = ctk.CTkEntry(
            row_log, font=self.font_entry, fg_color=WHITE,
            border_color=BORDER, text_color=TEXT_DARK,
            corner_radius=6, height=32,
        )
        self.entry_log.pack(side="left", fill="x", expand=True)
        self.btn_log = ctk.CTkButton(
            row_log, text="浏览", width=60, height=32,
            font=self.font_btn, fg_color=WHITE, text_color="#555",
            border_color=BORDER, border_width=1, corner_radius=6,
            hover_color="#e8e8ed",
            command=self._browse_file,
        )
        self.btn_log.pack(side="left", padx=(8, 0))

        # ── Output dir ──
        self.lbl_out = ctk.CTkLabel(
            self.window, text="输出目录", font=self.font_label,
            text_color=LABEL_GRAY,
        )
        self.lbl_out.pack(padx=pad_x, pady=(0, 2), anchor="w")

        row_out = ctk.CTkFrame(self.window, fg_color="transparent")
        row_out.pack(fill="x", padx=pad_x, pady=(0, pad_y))
        self.entry_out = ctk.CTkEntry(
            row_out, font=self.font_entry, fg_color=WHITE,
            border_color=BORDER, text_color=TEXT_DARK,
            corner_radius=6, height=32,
        )
        self.entry_out.pack(side="left", fill="x", expand=True)
        self.btn_out = ctk.CTkButton(
            row_out, text="浏览", width=60, height=32,
            font=self.font_btn, fg_color=WHITE, text_color="#555",
            border_color=BORDER, border_width=1, corner_radius=6,
            hover_color="#e8e8ed",
            command=self._browse_folder,
        )
        self.btn_out.pack(side="left", padx=(8, 0))

        # ── Week selection ──
        self.lbl_week = ctk.CTkLabel(
            self.window, text="选择周次", font=self.font_label,
            text_color=LABEL_GRAY,
        )
        self.lbl_week.pack(padx=pad_x, pady=(0, 2), anchor="w")

        self.opt_week = ctk.CTkOptionMenu(
            self.window, font=ctk.CTkFont(family="Microsoft YaHei UI", size=12),
            fg_color=WHITE, text_color=TEXT_DARK,
            button_color=BLUE, button_hover_color=BLUE_HOVER,
            corner_radius=6, height=32,
            values=["请先选择日志和输出目录"],
            command=self._on_week_change,
        )
        self.opt_week.pack(fill="x", padx=pad_x, pady=(0, pad_y))

        # ── Schedule toggle ──
        self.lbl_sched = ctk.CTkLabel(
            self.window, text="下周工作时间", font=self.font_label,
            text_color=LABEL_GRAY,
        )
        self.lbl_sched.pack(padx=pad_x, pady=(0, 2), anchor="w")

        row_sched = ctk.CTkFrame(self.window, fg_color="transparent")
        row_sched.pack(fill="x", padx=pad_x, pady=(0, pad_y))
        self.btn_5 = ctk.CTkButton(
            row_sched, text="1-5（5天）", width=120, height=30,
            font=self.font_btn, fg_color=BLUE, text_color=WHITE,
            corner_radius=6, hover_color=BLUE_HOVER,
            command=lambda: self._set_schedule(5),
        )
        self.btn_5.pack(side="left", padx=(0, 8))
        self.btn_6 = ctk.CTkButton(
            row_sched, text="1-5, 7（6天）", width=120, height=30,
            font=self.font_btn, fg_color=WHITE, text_color="#555",
            border_color=BORDER, border_width=1, corner_radius=6,
            hover_color="#e8e8ed",
            command=lambda: self._set_schedule(6),
        )
        self.btn_6.pack(side="left")

        # ── Generate button ──
        self.btn_gen = ctk.CTkButton(
            self.window, text="生成周报", height=38,
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=14, weight="bold"),
            fg_color=BLUE, text_color=WHITE,
            corner_radius=8, hover_color=BLUE_HOVER,
            command=self._generate,
        )
        self.btn_gen.pack(fill="x", padx=pad_x, pady=(pad_y + 8, pad_y))

        # ── Status message ──
        self.msg_var = ctk.StringVar(value="")
        self.lbl_msg = ctk.CTkLabel(
            self.window, textvariable=self.msg_var,
            font=self.font_msg, text_color=LABEL_GRAY,
        )
        self.lbl_msg.pack(padx=pad_x, pady=(0, 18))

    # ── Defaults ─────────────────────────────────────────
    def _get_default_log_path(self):
        """Auto-detect log file."""
        log = DATA_DIR / "工作日志 -2026.txt"
        if log.is_file():
            return str(log)
        return ""

    def _get_default_out_dir(self):
        out = DATA_DIR / "齐涛"
        return str(out)

    def _get_default_schedule(self):
        """Detect schedule: if last week has 5 entries, default to 6 days."""
        schedule = 5
        try:
            log_path = self._get_default_log_path()
            if log_path and Path(log_path).is_file():
                entries = parse_log(log_path)
                groups = group_by_project_week(entries)
                valid = sorted(w for w in groups if w >= 0)
                if valid:
                    last_week = groups[valid[-1]]
                    if len(last_week.entries) == 5:
                        schedule = 6
        except Exception:
            pass
        return schedule

    def _load_defaults(self):
        log_path = self._get_default_log_path()
        out_dir = self._get_default_out_dir()
        schedule = self._get_default_schedule()

        self.entry_log.delete(0, "end")
        self.entry_log.insert(0, log_path)
        self.entry_out.delete(0, "end")
        self.entry_out.insert(0, out_dir)
        self._set_schedule(schedule)
        self._refresh_weeks()

    # ── Actions ───────────────────────────────────────────
    def _browse_file(self):
        path = filedialog.askopenfilename(
            title="选择日志文件",
            initialdir=str(DATA_DIR),
            filetypes=[("文本文件", "*.txt")],
        )
        if path:
            self.entry_log.delete(0, "end")
            self.entry_log.insert(0, path)
            self._refresh_weeks()

    def _browse_folder(self):
        path = filedialog.askdirectory(
            title="选择输出目录",
            initialdir=str(DATA_DIR),
        )
        if path:
            self.entry_out.delete(0, "end")
            self.entry_out.insert(0, path)
            self._refresh_weeks()

    def _set_schedule(self, n):
        self.schedule_days = n
        if n == 5:
            self.btn_5.configure(fg_color=BLUE, text_color=WHITE,
                                 border_color="transparent")
            self.btn_6.configure(fg_color=WHITE, text_color="#555",
                                 border_color=BORDER)
        else:
            self.btn_6.configure(fg_color=BLUE, text_color=WHITE,
                                 border_color="transparent")
            self.btn_5.configure(fg_color=WHITE, text_color="#555",
                                 border_color=BORDER)

    def _refresh_weeks(self):
        log_path = self.entry_log.get().strip()
        out_dir = self.entry_out.get().strip()

        if not log_path or not out_dir:
            self.opt_week.configure(values=["请先选择日志和输出目录"])
            self.opt_week.set("请先选择日志和输出目录")
            return

        try:
            log = Path(log_path)
            out = Path(out_dir)
            if not log.is_file():
                self.opt_week.configure(values=["日志文件不存在"])
                self.opt_week.set("日志文件不存在")
                return

            entries = parse_log(str(log))
            groups = group_by_project_week(entries)
            existing = set()
            if out.is_dir():
                for f in out.iterdir():
                    if f.is_file() and f.suffix == '.txt':
                        m = re.search(r'第(\d+)周', f.name)
                        if m:
                            existing.add(int(m.group(1)))

            self.week_data.clear()
            options = []
            default_week = None
            for w in sorted(groups.keys(), reverse=True):
                if w < 0:
                    continue
                wg = groups[w]
                dr = format_date_range(wg.start_date, wg.end_date)
                done = w in existing
                self.week_data[w] = {"range": dr, "days": len(wg.entries), "done": done}
                label = f"第{w:02d}周  {dr}  {'✅' if done else '❌'}"
                options.append(label)
                if not done and default_week is None:
                    default_week = w

            if not options:
                self.opt_week.configure(values=["无可用周次"])
                self.opt_week.set("无可用周次")
                return

            self.week_options = list(self.week_data.keys())
            display_labels = [
                f"第{w:02d}周  {self.week_data[w]['range']}  {'✅' if self.week_data[w]['done'] else '❌'}"
                for w in sorted(self.week_data.keys(), reverse=True)
            ]
            self.opt_week.configure(values=display_labels)
            # Select first undone week, or first week
            target = default_week if default_week else sorted(self.week_data.keys(), reverse=True)[0]
            target_label = f"第{target:02d}周  {self.week_data[target]['range']}  {'✅' if self.week_data[target]['done'] else '❌'}"
            self.opt_week.set(target_label)
        except Exception as e:
            self.opt_week.configure(values=[f"解析失败: {e}"])
            self.opt_week.set(f"解析失败: {e}")

    def _on_week_change(self, choice):
        pass  # selection stored in opt_week, parsed on generate

    def _get_selected_week(self):
        """Parse the selected week number from the dropdown text."""
        choice = self.opt_week.get()
        m = re.search(r'第(\d+)周', choice)
        if m:
            return int(m.group(1))
        return None

    def _generate(self):
        log_path = self.entry_log.get().strip()
        out_dir = self.entry_out.get().strip()
        week_num = self._get_selected_week()

        if not log_path or not out_dir:
            self._show_msg("请填写日志文件和输出目录", error=True)
            return
        if week_num is None:
            self._show_msg("请选择有效的周次", error=True)
            return

        log = Path(log_path)
        out = Path(out_dir)
        if not log.is_file():
            self._show_msg(f"日志文件不存在: {log_path}", error=True)
            return
        if not out.is_dir():
            self._show_msg(f"输出目录不存在: {out_dir}", error=True)
            return

        self.btn_gen.configure(text="⏳ 生成中...", state="disabled")
        self.window.update()

        try:
            entries = parse_log(str(log))
            groups = group_by_project_week(entries)

            if week_num not in groups:
                self._show_msg(f"第{week_num}周无日志数据", error=True)
                return

            wg = groups[week_num]
            report = build_report(wg, self.schedule_days)
            text = render_report(report)

            filename = (
                f"TSSDPro项目组_齐涛_周报_"
                f"第{week_num:02d}周({wg.start_date.strftime('%Y.%m.%d')}"
                f"~{wg.end_date.strftime('%Y.%m.%d')}).txt"
            )
            filepath = out / filename
            filepath.write_text(text, encoding='utf-8')

            self._show_msg(f"✅ 第{week_num}周已生成 → {filename}", error=False)
            open_file(str(filepath))
            self._refresh_weeks()
        except Exception as e:
            self._show_msg(str(e), error=True)
        finally:
            self.btn_gen.configure(text="生成周报", state="normal")

    def _show_msg(self, text, error=False):
        self.msg_var.set(text)
        self.lbl_msg.configure(text_color=RED if error else GREEN if text.startswith("✅") else LABEL_GRAY)

    def run(self):
        self.window.mainloop()


def main():
    app = WeekReportApp()
    app.run()


if __name__ == '__main__':
    main()
