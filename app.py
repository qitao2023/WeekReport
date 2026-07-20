#!/usr/bin/env python3
"""周报生成器 - 原生桌面窗口"""
import json, os, re, sys, subprocess, platform
from pathlib import Path
import webview

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


class API:
    @staticmethod
    def _open_file(path):
        """Open a file with the default application, cross-platform."""
        if platform.system() == 'Windows':
            os.startfile(path)
        elif platform.system() == 'Darwin':
            subprocess.run(['open', path])
        else:
            subprocess.run(['xdg-open', path])

    def get_defaults(self):
        schedule_default = 5
        log_path = str(DATA_DIR / '工作日志 -2026.txt')

        # Auto-detect existing log files
        candidates = sorted(DATA_DIR.glob('工作日志*.txt'))
        if candidates:
            log_path = str(candidates[0])
            try:
                entries = parse_log(log_path)
                groups = group_by_project_week(entries)
                valid = sorted(w for w in groups if w >= 0)
                if valid:
                    last_week = groups[valid[-1]]
                    if len(last_week.entries) == 5:
                        schedule_default = 6
            except: pass

        # Auto-detect output dir
        out_dir = str(DATA_DIR / '齐涛')
        if not Path(out_dir).is_dir():
            alt = DATA_DIR / 'reports'
            if alt.is_dir():
                out_dir = str(alt)

        return json.dumps({
            'log': r'D:\66-工作日志\工作日志 -2026.txt',
            'out': r'E:\TSZNET\TSSDPro\Doc\02 Management\02项目组进度控制\02 Members Plan&Reprot\齐涛',
            'schedule': schedule_default,
        })

    def browse_file(self):
        result = window.create_file_dialog(webview.OPEN_DIALOG, directory=str(DATA_DIR), file_types=('文本文件 (*.txt)',))
        return result[0] if result else ''

    def browse_folder(self):
        result = window.create_file_dialog(webview.FOLDER_DIALOG, directory=str(DATA_DIR))
        return result[0] if result else ''

    def get_week_options(self, log_path, out_dir):
        """Return all weeks with status for dropdown."""
        try:
            log = Path(log_path)
            out = Path(out_dir)
            if not log_path:
                return json.dumps({'error': '请选择日志文件'})
            if not log.is_file():
                return json.dumps({'error': f'日志文件不存在：{log_path}'})
            entries = parse_log(str(log))
            groups = group_by_project_week(entries)

            if not groups:
                return json.dumps({'error': '日志文件中未找到工作记录'})

            existing = set()
            if out.is_dir():
                for f in out.iterdir():
                    if f.is_file() and f.suffix == '.txt':
                        m = re.search(r'第(\d+)周', f.name)
                        if m: existing.add(int(m.group(1)))

            options = []
            for w in sorted(groups.keys(), reverse=True):
                if w < 0: continue
                wg = groups[w]
                dr = format_date_range(wg.start_date, wg.end_date)
                done = w in existing
                options.append({
                    'week': w,
                    'range': dr,
                    'days': len(wg.entries),
                    'done': done,
                    'label': f"第{w:02d}周 {dr} {'✅' if done else '❌'}",
                })

            if not options:
                return json.dumps({'error': '未找到有效周次'})

            return json.dumps({'weeks': options}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({'error': f'解析失败：{e}'})

    def generate(self, log_path, out_dir, week_num, schedule_days=5):
        try:
            log = Path(log_path)
            out = Path(out_dir)
            if not log.is_file():
                return json.dumps({'ok': False, 'msg': f'日志文件不存在: {log_path}'})
            if not out.is_dir():
                return json.dumps({'ok': False, 'msg': f'输出目录不存在: {out_dir}'})

            entries = parse_log(str(log))
            groups = group_by_project_week(entries)
            week_num = int(week_num)

            if week_num not in groups:
                return json.dumps({'ok': False, 'msg': f'第{week_num}周无日志数据'})

            wg = groups[week_num]
            report = build_report(wg, int(schedule_days))
            text = render_report(report)

            filename = f"TSSDPro项目组_齐涛_周报_第{week_num:02d}周({wg.start_date.strftime('%Y.%m.%d')}~{wg.end_date.strftime('%Y.%m.%d')}).txt"
            filepath = out / filename
            filepath.write_text(text, encoding='utf-8')
            self._open_file(str(filepath))

            return json.dumps({'ok': True, 'msg': f'第{week_num}周已生成 → {filename}'})
        except Exception as e:
            return json.dumps({'ok': False, 'msg': str(e)})


HTML = r'''
<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:"Microsoft YaHei UI","PingFang SC",-apple-system,sans-serif;background:#f5f5f7;padding:24px 20px;overflow:hidden;user-select:none}
h2{font-size:17px;font-weight:700;color:#1d1d1f;margin-bottom:20px}
.row{margin-bottom:14px}
.row label{display:block;font-size:11px;color:#86868b;margin-bottom:4px;font-weight:600;text-transform:uppercase;letter-spacing:.3px}
.input-group{display:flex;gap:8px}
.input-group input{flex:1;padding:8px 10px;font-size:12px;font-family:"Cascadia Code","SF Mono",Menlo,Consolas,monospace;border:1px solid #d1d1d6;border-radius:6px;outline:none;background:#fff;-webkit-app-region:no-drag}
.input-group input:focus{border-color:#007AFF;box-shadow:0 0 0 2px rgba(0,122,255,0.15)}
.browse-btn{padding:8px 12px;font-size:12px;font-weight:500;border:1px solid #d1d1d6;border-radius:6px;background:#fff;color:#555;cursor:pointer;white-space:nowrap;-webkit-app-region:no-drag}
.browse-btn:hover{background:#e8e8ed}
.toggle-group{display:flex;gap:8px}
.toggle-btn{padding:6px 16px;font-size:12px;font-weight:500;border:1px solid #d1d1d6;border-radius:6px;background:#fff;color:#555;cursor:pointer;-webkit-app-region:no-drag}
.toggle-btn.active{background:#007AFF;color:#fff;border-color:#007AFF}
select{width:100%;padding:8px 10px;font-size:13px;border:1px solid #d1d1d6;border-radius:6px;outline:none;background:#fff;-webkit-app-region:no-drag}
select:focus{border-color:#007AFF}
.btn{width:100%;padding:10px;font-size:14px;font-weight:600;border:none;border-radius:8px;background:#007AFF;color:#fff;cursor:pointer;-webkit-app-region:no-drag}
.btn:hover{background:#0062cc}
.btn:disabled{opacity:.5}
.msg{margin-top:12px;text-align:center;font-size:13px;color:#86868b;min-height:18px}
.msg.ok{color:#34c759}.msg.err{color:#ff3b30}
</style></head>
<body>
<div class="row"><label>日志文件</label><div class="input-group"><input id="logPath"><button class="browse-btn" onclick="browseFile()">浏览</button></div></div>
<div class="row"><label>输出目录</label><div class="input-group"><input id="outDir"><button class="browse-btn" onclick="browseFolder()">浏览</button></div></div>
<div class="row"><label>选择周次</label><div class="input-group"><select id="weekSelect" onchange="onWeekChange()" onfocus="loadWeeks()" style="flex:1"></select><button class="browse-btn" onclick="loadWeeks()" title="刷新周次列表">🔄</button></div></div>
<div class="row"><label>下周工作时间</label><div class="toggle-group"><button class="toggle-btn active" id="btn5" onclick="setSchedule(5)">1-5 (5天)</button><button class="toggle-btn" id="btn6" onclick="setSchedule(6)">1-5,7 (6天)</button></div></div>
<button class="btn" id="btn" onclick="generate()">生成周报</button>
<div class="msg" id="msg"></div>
<script>
let scheduleDays=5;
let weekOptions=[];

function setSchedule(n){
  scheduleDays=n;
  document.getElementById('btn5').className=n===5?'toggle-btn active':'toggle-btn';
  document.getElementById('btn6').className=n===6?'toggle-btn active':'toggle-btn';
}

async function loadWeeks(){
  const log=document.getElementById('logPath').value.trim();
  const out=document.getElementById('outDir').value.trim();
  if(!log||!out) return;
  const r=await pywebview.api.get_week_options(log,out);
  const data=JSON.parse(r);
  const sel=document.getElementById('weekSelect');
  if(data.error){
    sel.innerHTML='<option value="">'+data.error+'</option>';
    document.getElementById('btn').disabled=true;
    return;
  }
  weekOptions=data.weeks;
  sel.innerHTML=weekOptions.map(o=>'<option value="'+o.week+'">'+o.label+'</option>').join('');
  document.getElementById('btn').disabled=false;
}

function onWeekChange(){}

async function init(){
  const r=await pywebview.api.get_defaults();
  const d=JSON.parse(r);
  document.getElementById('logPath').value=d.log;
  document.getElementById('outDir').value=d.out;
  setSchedule(d.schedule||5);
  await loadWeeks();
}

async function browseFile(){
  const r=await pywebview.api.browse_file();
  if(r){document.getElementById('logPath').value=r;await loadWeeks();}
}
async function browseFolder(){
  const r=await pywebview.api.browse_folder();
  if(r){document.getElementById('outDir').value=r;await loadWeeks();}
}

document.getElementById('logPath').addEventListener('change',loadWeeks);
document.getElementById('outDir').addEventListener('change',loadWeeks);

async function generate(){
  const btn=document.getElementById('btn');
  const msg=document.getElementById('msg');
  const log=document.getElementById('logPath').value.trim();
  const out=document.getElementById('outDir').value.trim();
  const week=document.getElementById('weekSelect').value;
  if(!log||!out){msg.className='msg err';msg.textContent='请填写日志文件和输出目录';return}
  if(!week){msg.className='msg err';msg.textContent='请选择有效的周次';return}
  btn.disabled=true;btn.textContent='⏳ 生成中...';msg.className='msg';msg.textContent='';
  const r=await pywebview.api.generate(log,out,week,scheduleDays);
  const d=JSON.parse(r);
  msg.className=d.ok?'msg ok':'msg err';
  msg.textContent=d.msg;
  btn.disabled=false;btn.textContent='生成周报';
  if(d.ok) await loadWeeks();
}

window.addEventListener('pywebviewready',async function(){await init();});
</script>
</body></html>
'''


def main():
    global window
    api = API()
    window = webview.create_window(
        title='周报工具',
        html=HTML,
        js_api=api,
        width=500,
        height=420,
        resizable=True,
    )
    webview.start()


if __name__ == '__main__':
    main()
