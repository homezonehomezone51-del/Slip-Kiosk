"""Slip Kiosk - prints an attendance + leave slip for every punch. Needs slip_bridge.py next to it.
Reports: copy the raw WH / LB files (name must contain WH or LB) into the 'reports' folder - they are converted and loaded automatically."""
import base64, hashlib, hmac, io, json, os, queue, re, secrets, shutil, sys, threading
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, scrolledtext, simpledialog, ttk
import pandas as pd
from PIL import Image                      # needed for the system tray icon - add to exe build
import pystray                              # needed for the system tray icon - add to exe build

LOGO_B64 = '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'
BASE = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
DATA = os.path.join(BASE, 'reports')
# settings file lives in %APPDATA%\SlipKiosk (hidden from the exe folder); an old config.json next to the exe is moved there once
CFG_DIR = os.path.join(os.environ.get('APPDATA') or BASE, 'SlipKiosk')
CFG, OLD_CFG = os.path.join(CFG_DIR, 'config.json'), os.path.join(BASE, 'config.json')
try:
    os.makedirs(CFG_DIR, exist_ok=True)
    if not os.path.exists(CFG) and os.path.exists(OLD_CFG): shutil.move(OLD_CFG, CFG)
except OSError:
    CFG = OLD_CFG
STATE = os.path.join(CFG_DIR, 'data')                  # cache, processed raw files, cache.json: all kept here (next to config.json), so the reports folder only shows WH / LB
try: os.makedirs(STATE, exist_ok=True)
except OSError: STATE = CFG_DIR
os.makedirs(DATA, exist_ok=True)
os.chdir(DATA)
q = queue.Queue()


class W:                                   # send all print() output to the log window
    def write(self, s): q.put(s)
    def flush(self): pass


sys.stdout = W()
# ---- speed: reading a big .xlsx with pandas takes ~15 s, so the parsed table is cached once and reused (restart, re-check, auto-update) ----
import hashlib, pickle, zipfile
CACHE = os.path.join(STATE, 'cache')
_real_read_excel = pd.read_excel


def _cached_read_excel(io_, *a, **k):
    try:
        p = os.fspath(io_)
        base = os.path.basename(p).lower()
        if base.endswith(('.xlsx', '.xlsx.tmp')) and re.match(r'^(wh|lb) \(', base) and os.path.isfile(p):
            st = os.stat(p)
            key = hashlib.md5(repr((st.st_size, st.st_mtime_ns, a, sorted((x, repr(y)) for x, y in k.items()))).encode()).hexdigest()
            cp = os.path.join(CACHE, key + '.pkl')
            if os.path.isfile(cp):
                try: return pickle.load(open(cp, 'rb'))
                except Exception: pass
            df = _real_read_excel(io_, *a, **k)
            try:
                os.makedirs(CACHE, exist_ok=True)
                for old in sorted((os.path.join(CACHE, x) for x in os.listdir(CACHE)), key=os.path.getmtime)[:-8]: os.remove(old)   # keep the 8 newest
                pickle.dump(df, open(cp + '.t', 'wb'), protocol=4); os.replace(cp + '.t', cp)
            except Exception: pass
            return df
    except Exception:
        pass
    return _real_read_excel(io_, *a, **k)


pd.read_excel = _cached_read_excel                       # must happen before slip_bridge is imported

import slip_bridge as sb                   # engine: reads the newest reports in the current folder

# ---- keep the reports folder clean: files other than WH / LB reports live in STATE (C:\Users\<user>\AppData\Roaming\SlipKiosk\data) ----
def _to_state(p):
    """Path of a bridge housekeeping file ('cache.json...') inside the reports folder -> same name inside STATE."""
    try:
        s = os.fspath(p)
        if isinstance(s, str) and os.path.basename(s).startswith('cache.json') and \
                os.path.normcase(os.path.abspath(os.path.dirname(s) or '.')) == os.path.normcase(os.path.abspath(DATA)):
            return os.path.join(STATE, os.path.basename(s))
    except Exception:
        pass
    return p


def _wrap1(mod, name):
    f = getattr(mod, name)
    setattr(mod, name, lambda p, *a, **k: f(_to_state(p), *a, **k))


def _wrap2(mod, name):
    f = getattr(mod, name)
    setattr(mod, name, lambda s, d, *a, **k: f(_to_state(s), _to_state(d), *a, **k))


for _f in ('cache.json',):                                            # move what an older version left in the reports folder
    try:
        _o = os.path.join(DATA, _f)
        if os.path.isfile(_o):
            if not os.path.exists(os.path.join(STATE, _f)): shutil.move(_o, os.path.join(STATE, _f))
            else: os.remove(_o)
    except Exception:
        pass
try:
    shutil.rmtree(os.path.join(DATA, '.cache'), ignore_errors=True)    # old parsed-table cache (rebuilt automatically in STATE)
    _op = os.path.join(DATA, 'processed')
    if os.path.isdir(_op):
        os.makedirs(os.path.join(STATE, 'processed'), exist_ok=True)
        for _r, _d, _fs in os.walk(_op):
            for _f in _fs:
                _t = os.path.join(STATE, 'processed', os.path.relpath(os.path.join(_r, _f), _op)); os.makedirs(os.path.dirname(_t), exist_ok=True)
                try: shutil.move(os.path.join(_r, _f), _t)
                except OSError: pass
        shutil.rmtree(_op, ignore_errors=True)
    for _f in os.listdir(DATA):                                       # leftovers of an interrupted conversion
        if re.match(r'^(WH|LB) \(.*\.(tmp|norm)$', _f, re.I):
            try: os.remove(os.path.join(DATA, _f))
            except OSError: pass
except Exception:
    pass

try:
    import builtins
    _wrap1(builtins, 'open')
    for _n in ('stat', 'remove', 'unlink'): _wrap1(os, _n)
    for _n in ('exists', 'isfile', 'getmtime', 'getsize'): _wrap1(os.path, _n)
    for _n in ('replace', 'rename'): _wrap2(os, _n)
    for _n in dir(sb):                                                # if the bridge keeps the file name in a variable, point it at STATE too
        _v = getattr(sb, _n, None)
        if isinstance(_v, str) and os.path.basename(_v).startswith('cache.json') and _n.isupper(): setattr(sb, _n, os.path.join(STATE, os.path.basename(_v)))
except Exception:
    pass


# ---- auto-fix raw HR exports: the exe accepts the report exactly as downloaded (no manual editing needed) ----
def _fast_drop_top_rows(raw, h):
    """Very fast fix for a plain sheet (no merged cells / formulas): delete rows 1..h-1 straight in the XML. Returns new bytes or None."""
    z = zipfile.ZipFile(io.BytesIO(raw)); names = z.namelist()
    sheets = [n for n in names if re.match(r'xl/worksheets/sheet\d+\.xml$', n)]
    if len(sheets) != 1: return None
    x = z.read(sheets[0]).decode('utf-8')
    if '<mergeCell' in x or '<f>' in x or '<f ' in x or 'inlineStr' in x or '<tableParts' in x: return None
    a, b = x.find('<sheetData>'), x.find('</sheetData>')
    i = x.find(f'<row r="{h}"')
    if a < 0 or b < 0 or i < 0: return None
    body = x[i:b]
    d = h - 1
    body = re.sub(r'<row r="(\d+)"', lambda m: f'<row r="{int(m.group(1)) - d}"', body)
    body = re.sub(r'<c r="([A-Z]+)(\d+)"', lambda m: f'<c r="{m.group(1)}{int(m.group(2)) - d}"', body)
    head = re.sub(r'<dimension ref="[^"]*"/>', lambda m: re.sub(r'(\d+)(?!.*\d)', lambda n: str(int(n.group(1)) - d), m.group(0)), x[:a])
    new = head + '<sheetData>' + body + x[b:]
    # Emp Id must be numeric in the sheet (text such as "906137 (906137)" needs the slower, thorough path)
    hdr = re.search(r'<row r="1"[^>]*>(.*?)</row>', body, re.S).group(1)
    ss = re.findall(r'<si>(.*?)</si>', z.read('xl/sharedStrings.xml').decode('utf-8'), re.S) if 'xl/sharedStrings.xml' in names else []
    col = None
    for m in re.finditer(r'<c r="([A-Z]+)1"[^>]*t="s"[^>]*><v>(\d+)</v>', hdr):
        if re.sub(r'<[^>]+>', '', ss[int(m.group(2))]).strip() == 'Emp Id': col = m.group(1)
    if col is None or len(re.findall(rf'<c r="{col}\d+"[^>]*t="s"', new)) != 1: return None
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zo:
        for n in names: zo.writestr(n, new.encode('utf-8') if n == sheets[0] else z.read(n))
    return out.getvalue()


def normalize_report(path, kind):
    """Raw WH/LB .xlsx export -> clean table: header on row 1, one header row, numeric Emp Id. Safe to run twice."""
    import openpyxl
    from openpyxl.cell import WriteOnlyCell
    if os.path.splitext(path.replace('.tmp', ''))[1].lower() != '.xlsx': return       # .xls files are left untouched
    raw = open(path, 'rb').read()
    ro = openpyxl.load_workbook(io.BytesIO(raw), read_only=True); sh = ro.active
    head = list(sh.iter_rows(min_row=1, max_row=41, values_only=True))
    h = next((r for r, row in enumerate(head, 1) if any(str(v).strip() == 'Emp Id' for v in row if v is not None)), None)
    if h is None: ro.close(); return
    nxt = head[h] if h < len(head) else ()
    two = kind == 'LB' and any(str(v).strip() in ('Allowed', 'Availed', 'Closing') for v in nxt if v is not None)
    if h == 1 and not two: ro.close(); return                                          # already clean
    if not two:                                                                        # plain sheet: fix straight in the XML (seconds, not minutes)
        ro.close(); fast = _fast_drop_top_rows(raw, h)
        if fast:
            tmp = path + '.norm'; open(tmp, 'wb').write(fast); os.replace(tmp, path); return
        ro = openpyxl.load_workbook(io.BytesIO(raw), read_only=True); sh = ro.active
    top = list(head[h - 1]); sub = list(head[h]) if two else [None] * len(top)
    n = max(i for i, v in enumerate(top) if v is not None) + 1
    if two: n = max(n, max((i for i, v in enumerate(sub) if v is not None), default=0) + 1)
    top, sub = (top + [None] * n)[:n], (sub + [None] * n)[:n]
    names, cur = [], None
    for i in range(n):
        if top[i] is not None: cur = str(top[i]).strip()
        names.append(cur if sub[i] is None else f'{cur} {str(sub[i]).strip()}')
    ec = names.index('Emp Id')
    out = openpyxl.Workbook(write_only=True); ws = out.create_sheet('LeaveReport' if kind == 'LB' else 'Report')
    ws.append(names)
    for row in sh.iter_rows(min_row=h + (2 if two else 1), max_col=n):
        row = list(row) + [None] * (n - len(row))
        v = row[ec].value
        m = re.match(r'\s*(\d+)\s*(\(|$)', str(v)) if v is not None else None
        if not m: continue                                                              # blank / footer rows
        cells = []
        for j, c in enumerate(row):
            val = int(m.group(1)) if j == ec else c.value
            nf = getattr(c, 'number_format', 'General')
            if val is not None and nf and nf != 'General' and j != ec:
                wc = WriteOnlyCell(ws, value=val); wc.number_format = nf; cells.append(wc)
            else: cells.append(val)
        ws.append(cells)
    ro.close(); tmp = path + '.norm'; out.save(tmp); os.replace(tmp, path)


_orig_check, _orig_refresh, _seen = sb.check_file, sb.refresh, {}
def _check_file(path, kind, *a, **k):
    try: normalize_report(path, kind)
    except Exception as e: print(f'Could not auto-fix {os.path.basename(path)}: {e}')
    return _orig_check(path, kind, *a, **k)
def _refresh(*a, **k):                                   # also fixes reports that arrived through the linked-folder auto-update
    for f in os.listdir(DATA):
        m = re.match(r'^(WH|LB) \(', f)
        p = os.path.join(DATA, f)
        if m and f.lower().endswith('.xlsx') and _seen.get(p) != os.path.getmtime(p):
            try: normalize_report(p, m.group(1))
            except Exception as e: print(f'Could not auto-fix {f}: {e}')
            _seen[p] = os.path.getmtime(p)
    return _orig_refresh(*a, **k)
sb.check_file, sb.refresh = _check_file, _refresh

# ======================================================================================================================
# AUTO REPORT INGEST: drop the raw HR exports (WH / LB, .xls that is really HTML, or real .xls/.xlsx) into the reports folder
# and they are converted + loaded by themselves within seconds. No Excel, no manual "Save as .xlsx".
#   * file name only has to contain WH or LB as a word (WH__05_Nov__2026_.xls, LB report.xls, WH (05 Nov, 2026) (1).xls ...)
#   * date is taken from the name when there is one, otherwise from the file's modified date
#   * new files are picked up every WATCH_SEC seconds once they have finished copying; the old data keeps serving slips meanwhile
# ======================================================================================================================
import time, zipfile as _zf
from datetime import date as _date, timedelta as _td
from xml.sax.saxutils import escape as _xesc

WATCH_SEC = 5                                                    # folder is looked at every 5 s (a file is taken once its size stopped changing)
PROCESSED = os.path.join(STATE, 'processed')                     # raw files are moved here (C:\Users\...\AppData\Roaming\SlipKiosk\data), NOT into the reports folder
KIND_RE = re.compile(r'(?<![A-Za-z])(WH|LB)(?![A-Za-z])', re.I)  # WH / LB as a separate word: 'WH__05_Nov', 'lb report', 'WH-new'
DATE_RE = re.compile(r'(\d{1,2})[\s_\-.]+([A-Za-z]{3,9})[\s_,.\-]*(\d{4})')
CANON_RE = re.compile(r'^(WH|LB) \((\d{2}) ([A-Za-z]{3}), (\d{4})\)\.(xlsx?)$')     # the name the engine reads: 'WH (05 Nov, 2026).xlsx'
SKIP_RE = re.compile(r'^(~\$|\.)|\.(tmp|part|crdownload|norm|bak|lnk)$', re.I)
REPORT_EXT = ('.xls', '.xlsx', '.xlsm', '.htm', '.html')
MONTHS = {m: i for i, m in enumerate(['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'], 1)}
WATCH = {'result': 'starting...', 'last': '-'}
ING_LOCK = threading.Lock()                                      # one load at a time (watcher and the manual buttons)


def _log(msg): print(f'[{datetime.now():%H:%M:%S}] {msg}')


# ---------- HTML table (what the HR system calls ".xls") -> clean .xlsx, written straight as XML (seconds, not minutes) ----------
_TR = re.compile(r'<tr(?:\s[^>]*)?>', re.I)
_CELL = re.compile(r'<(t[dh])([^>]*)>(.*?)</t[dh]>', re.I | re.S)
_TAG = re.compile(r'<[^>]+>')
_SPAN = re.compile(r'(colspan|rowspan)\s*=\s*["\']?(\d+)', re.I)
_BAD = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')
_NUM, _DMY = re.compile(r'^-?\d+(?:\.\d+)?$'), re.compile(r'^(\d{1,2})[ \-]([A-Za-z]{3})[A-Za-z]*[ \-,]*(\d{4})$')
_MDY, _HM = re.compile(r'^(\d{1,2})/(\d{1,2})/(\d{4})$'), re.compile(r'^(\d{1,3}):(\d{1,2})$')
_EPOCH = _date(1899, 12, 30)
_COLS = []


def _col(i):
    while len(_COLS) <= i:
        n, s = len(_COLS), ''
        n += 1
        while n: n, r = divmod(n - 1, 26); s = chr(65 + r) + s
        _COLS.append(s)
    return _COLS[i]


def _typed(t):
    """Same typing Excel does when it opens the HTML: numbers, dates and times become real values. Returns (attrs, inner)."""
    if _NUM.match(t): return '', f'<v>{t}</v>'
    m = _DMY.match(t)
    if m and m.group(2).lower() in MONTHS:
        try: return ' s="1"', f'<v>{(_date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1))) - _EPOCH).days}</v>'
        except ValueError: pass
    m = _MDY.match(t)                                                       # DOJ is month/day/year in this export (10/19/2021)
    if m:
        try: return ' s="2"', f'<v>{(_date(int(m.group(3)), int(m.group(1)), int(m.group(2))) - _EPOCH).days}</v>'
        except ValueError: pass
    m = _HM.match(t)
    if m and int(m.group(2)) < 60:
        h, mi = int(m.group(1)), int(m.group(2))
        return (' s="3"' if h < 24 else ' s="4"'), f'<v>{(h * 60 + mi) / 1440!r}</v>'
    return ' t="inlineStr"', f'<is><t>{_xesc(_BAD.sub("", t))}</t></is>'


def _text(x):
    if '<' in x: x = _TAG.sub('', x)
    if '&' in x: import html; x = html.unescape(x)
    return x.replace('\xa0', ' ').strip()


def _html_rows(path):
    """Yield the <tr> bodies of a (possibly 70 MB) HTML export without loading it all."""
    buf, end = '', re.compile('</tr>', re.I)
    with open(path, 'r', encoding='utf-8-sig', errors='replace', newline='') as f:
        while True:
            ch = f.read(1 << 22)
            if not ch: break
            buf += ch
            parts = end.split(buf); buf = parts.pop()
            for p in parts:
                m = _TR.search(p)
                if m: yield p[m.end():]


_STYLES = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
           '<numFmts count="2"><numFmt numFmtId="164" formatCode="dd mmm yyyy"/><numFmt numFmtId="165" formatCode="[h]:mm"/></numFmts>'
           '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
           '<fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>'
           '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
           '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="5">'
           '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
           '<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
           '<xf numFmtId="14" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
           '<xf numFmtId="20" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
           '<xf numFmtId="165" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/></cellXfs>'
           '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>')


def _attr(p, a):
    try:
        import ctypes; ctypes.windll.kernel32.SetFileAttributesW(str(p), a)       # 0x02 hidden, 0x80 normal (Windows only)
    except Exception:
        pass


def _open_hidden(p):
    """Working file that Explorer does not show while it is being written."""
    if os.path.exists(p): _attr(p, 0x80)
    open(p, 'wb').close(); _attr(p, 0x02)
    return open(p, 'r+b')


def html_to_xlsx(src, kind, out):
    """Raw WH / LB HTML export -> clean .xlsx (header on row 1, one header row, numeric Emp Id) - exactly what normalize_report produces.
    Returns the number of employee/attendance rows written."""
    rows = _html_rows(src)
    names = None
    for r in rows:                                                          # ---- header (WH: one row, LB: two rows with merged cells)
        if '<th' not in r.lower(): continue
        top = [(_text(c[2]), int(dict((a.lower(), b) for a, b in _SPAN.findall(c[1])).get('colspan', 1)),
                int(dict((a.lower(), b) for a, b in _SPAN.findall(c[1])).get('rowspan', 1))) for c in _CELL.findall(r)]
        slots = [(t, rs) for t, cs, rs in top for _ in range(cs)]
        if any(rs > 1 for _, rs in slots):
            sub = [_text(c[2]) for c in _CELL.findall(next(rows))]
            it, names = iter(sub), []
            for t, rs in slots: names.append(t if rs > 1 else f'{t} {next(it, "")}'.strip())
        else:
            names = [t for t, _ in slots]
        break
    if not names or 'Emp Id' not in names: raise ValueError('No "Emp Id" column found - this is not a WH / LB report')
    if kind == 'WH' and 'Attendance Date' not in names: raise ValueError('This file is not a WH (attendance) report')
    if kind == 'LB' and not any(n.endswith('Allowed') for n in names): raise ValueError('This file is not an LB (leave balance) report')
    n, ec, count = len(names), names.index('Emp Id'), 0
    cache, cols = {}, [_col(i) for i in range(len(names))]
    with _open_hidden(out) as fh, _zf.ZipFile(fh, 'w', _zf.ZIP_DEFLATED, compresslevel=1) as z:
        z.writestr('[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                   '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>')
        z.writestr('_rels/.rels', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr('xl/workbook.xml', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
                   f'<sheet name="{"LeaveReport" if kind == "LB" else "Report"}" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
                   '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
        z.writestr('xl/styles.xml', _STYLES)
        with z.open('xl/worksheets/sheet1.xml', 'w', force_zip64=True) as w:
            w.write(('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>').encode())
            hdr = ''.join(f'<c r="{cols[i]}1" t="inlineStr"><is><t>{_xesc(_BAD.sub("", t))}</t></is></c>' for i, t in enumerate(names))
            buf = [f'<row r="1">{hdr}</row>']
            for r in rows:
                cells = _CELL.findall(r)
                if len(cells) < ec + 1: continue
                m = re.match(r'\s*(\d+)\s*(\(|$)', _text(cells[ec][2]))
                if not m: continue                                           # blank / footer rows
                count += 1; rn = count + 1; out_cells = []
                for j in range(min(n, len(cells))):
                    t = str(int(m.group(1))) if j == ec else _text(cells[j][2])
                    if not t: continue
                    f = cache.get(t)
                    if f is None:
                        f = cache[t] = _typed(t)
                        if len(cache) > 400000: cache.clear()
                    out_cells.append(f'<c r="{cols[j]}{rn}"{f[0]}>{f[1]}</c>')
                buf.append(f'<row r="{rn}">{"".join(out_cells)}</row>')
                if len(buf) >= 4000: w.write(''.join(buf).encode()); buf = []
            buf.append('</sheetData></worksheet>'); w.write(''.join(buf).encode())
    if count == 0: raise ValueError('The report has no employee rows')
    return count


# ---------- decide what a dropped file is, convert it, hand it to the engine ----------
def sniff(path):
    with open(path, 'rb') as f: head = f.read(4096)
    if head[:2] == b'PK': return 'xlsx'
    if head[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1': return 'xls'
    low = head.lower()
    if b'<html' in low or b'<table' in low or b'<tr' in low or b'<body' in low: return 'html'
    return 'unknown'


def file_kind(name):
    ks = {m.group(1).upper() for m in KIND_RE.finditer(os.path.splitext(name)[0])}
    return ks.pop() if len(ks) == 1 else None


def file_date(path):
    m = DATE_RE.search(os.path.splitext(os.path.basename(path))[0])
    if m and m.group(2)[:3].lower() in MONTHS:
        try: return _date(int(m.group(3)), MONTHS[m.group(2)[:3].lower()], int(m.group(1)))
        except ValueError: pass
    return datetime.fromtimestamp(os.path.getmtime(path)).date()             # no date in the name -> the day the file was saved


def _loaded_date(kind):
    try:
        d = sb.report_dates().get(kind)
        return d.date() if isinstance(d, datetime) else d
    except Exception:
        return None


def _prune(kind):
    """Keep the 3 newest loaded reports and the 3 newest raw files per kind, so the folders never fill up."""
    try:
        have = []
        for f in os.listdir(DATA):
            m = CANON_RE.match(f)
            if m and m.group(1) == kind:
                have.append((datetime.strptime(f'{m.group(2)} {m.group(3).title()} {m.group(4)}', '%d %b %Y'), f))
        for _, f in sorted(have, reverse=True)[3:]: os.remove(os.path.join(DATA, f))
        if os.path.isdir(PROCESSED):
            raw = sorted((os.path.join(PROCESSED, f) for f in os.listdir(PROCESSED) if file_kind(f) == kind and os.path.isfile(os.path.join(PROCESSED, f))), key=os.path.getmtime, reverse=True)
            for p in raw[3:]: os.remove(p)
    except Exception:
        pass


def ingest(src, kind, d=None):
    """Convert (if needed) and load one report. Raises on a bad file. Returns (text for the log, path of the clean report)."""
    d = d or file_date(src)
    t0, fmt = time.time(), sniff(src)
    if fmt == 'unknown': raise ValueError('not an Excel / HTML report file')
    ext = '.xls' if fmt == 'xls' else '.xlsx'
    dst = os.path.join(DATA, f'{kind} ({d:%d %b}, {d:%Y}){ext}')
    same = os.path.abspath(src) == os.path.abspath(dst) and fmt != 'html'     # already a clean report with the right name
    with ING_LOCK:
        tmp, rows = dst + '.tmp', None
        try:
            if same: sb.check_file(dst, kind)
            else:
                if fmt == 'html': rows = html_to_xlsx(src, kind, tmp)
                else:
                    with _open_hidden(tmp) as o, open(src, 'rb') as i: shutil.copyfileobj(i, o, 1 << 20)
                sb.check_file(tmp, kind)                                    # engine validates the file (and caches the parsed table)
                _attr(tmp, 0x80); os.replace(tmp, dst)
        except Exception:
            try: os.remove(tmp)
            except OSError: pass
            raise
        other = dst[:-len(ext)] + ('.xls' if ext == '.xlsx' else '.xlsx')    # never keep two files for the same report date
        if os.path.isfile(other) and os.path.abspath(other) != os.path.abspath(src):
            try: os.remove(other)
            except OSError: pass
        _prune(kind)
        sb.refresh()
    return f'{kind} report {d:%d %b %Y} loaded' + (f' ({rows} rows)' if rows else '') + f' in {time.time() - t0:.0f}s', dst


def _archive(path, sub=''):
    """Move a raw file out of the reports folder (the engine must only see clean files): loaded -> processed, bad/older -> processed/rejected."""
    try:
        os.makedirs(os.path.join(PROCESSED, sub), exist_ok=True)
        dst = os.path.join(PROCESSED, sub, os.path.basename(path))
        if os.path.exists(dst): dst = os.path.splitext(dst)[0] + f'_{datetime.now():%H%M%S}' + os.path.splitext(dst)[1]
        shutil.move(path, dst)
    except Exception as e:
        _log(f'Could not move {os.path.basename(path)} to processed: {e}')


def watcher():
    seen, stable, failed, ignored, ready_sig = {}, {}, {}, set(), {}
    time.sleep(8)                                                           # let the first start-up load finish
    first = True
    while True:                                                             # runs for as long as the app runs (Stop button only stops the machine link)
        try:
            folders = [DATA] + ([cfg['source_dir']] if cfg.get('source_dir') and os.path.isdir(cfg['source_dir']) else [])
            cands, refresh_needed = {}, False
            for folder in folders:
                for name in os.listdir(folder):
                    path = os.path.join(folder, name)
                    ext = os.path.splitext(name)[1].lower()
                    if SKIP_RE.search(name) or ext not in REPORT_EXT or not os.path.isfile(path): continue
                    kind = file_kind(name)
                    if not kind:
                        if path not in ignored: ignored.add(path); _log(f'Ignored {name}: the file name must contain WH or LB')
                        continue
                    st = os.stat(path); sig = (st.st_size, st.st_mtime_ns)
                    if folder == DATA and CANON_RE.match(name) and ext == '.xlsx':           # already a clean report from this app / Excel
                        if ready_sig.get(path) != sig:
                            if not first: refresh_needed = True                              # a clean file appeared / changed after start-up
                            ready_sig[path] = sig
                        continue
                    if seen.get(path) == sig or failed.get(path) == sig: continue
                    prev = stable.get(path)
                    if not prev or prev != sig: stable[path] = sig; continue                # size/date still changing: wait one more round
                    try: open(path, 'rb').close()
                    except OSError: continue                                                # still locked by the copy / download
                    cands.setdefault(kind, []).append((file_date(path), st.st_mtime_ns, path, sig, folder))
            for kind, lst in cands.items():
                lst.sort(key=lambda x: (x[0], x[1]))
                for d, _, path, sig, folder in lst[:-1]:                                    # several files of one kind: only the newest is loaded
                    seen[path] = sig; _log(f'Skipped {os.path.basename(path)}: a newer {kind} file is present')
                    if folder == DATA: _archive(path, 'rejected')
                d, _, path, sig, folder = lst[-1]
                name, cur = os.path.basename(path), _loaded_date(kind)
                if cur and d < cur:
                    seen[path] = sig; _log(f'Ignored {name}: loaded {kind} report is dated {cur:%d %b %Y}, this one ({d:%d %b %Y}) is older')
                    if folder == DATA: _archive(path, 'rejected')
                    continue
                if folder != DATA:                                                           # linked folder: do nothing if it was already loaded
                    done = os.path.join(DATA, f'{kind} ({d:%d %b}, {d:%Y})')
                    for e in ('.xlsx', '.xls'):
                        if os.path.isfile(done + e) and os.path.getmtime(done + e) >= os.path.getmtime(path): seen[path] = sig
                    if seen.get(path) == sig: continue
                WATCH['result'] = f'loading {name} ...'; _log(f'Found {name} - loading')
                try:
                    msg, dst = ingest(path, kind, d)
                    seen[path] = sig; WATCH['last'] = f'{datetime.now():%d %b %H:%M:%S}  {msg}'; _log(msg)
                    if dst.lower().endswith('.xlsx'): s2 = os.stat(dst); ready_sig[dst] = (s2.st_size, s2.st_mtime_ns)    # our own output: no second reload
                    if folder == DATA and os.path.abspath(path) != os.path.abspath(dst): _archive(path)
                except Exception as e:
                    failed[path] = sig; WATCH['last'] = f'{datetime.now():%d %b %H:%M:%S}  FAILED {name}'; _log(f'Could not load {name}: {e}')
                    if folder == DATA: _archive(path, 'rejected')
            if refresh_needed and not cands:
                _log('Clean report file changed - reloading'); sb.refresh()
            first = False
            WATCH['result'] = f'watching every {WATCH_SEC} s'
        except Exception as e:
            WATCH['result'] = f'error: {e}'
        time.sleep(WATCH_SEC)


cfg = {'device_ip': '192.168.1.201', 'device_port': '4370', 'comm_key': '0', 'printer_ip': '192.168.1.250',
       'paper': '80', 'days': '30', 'mode': 'network', 'printer_name': '', 'source_dir': '', 'sync_min': '60', 'plain': False, 'autorun': False}
if os.path.exists(CFG):
    cfg.update(json.load(open(CFG)))
BAT = os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup', 'SlipKiosk.bat')
RED, NAVY, BG, FN = '#c8000f', '#111111', '#ffffff', ('Segoe UI', 10)          # Servis Tyres logo: red, black, white
INK, MUTED, LINE = '#1a1a1a', '#6b6b6b', '#e3e3e3'
HEAD, PRIMARY, PRIMARY_D = '#ffffff', '#c8000f', '#a3040c'                       # black header | logo red | darker red (hover)
NAME = {k: re.compile(rf'^{k}[\s_]*\(?[\s_]*(\d{{1,2}})[\s_\-]+([A-Za-z]{{3,9}})[\s_,.\-]*(\d{{4}})[\s_]*\)?(?:[\s_]*\(\d+\))?\.xlsx?$', re.I) for k in ('WH', 'LB')}   # tolerant: 'LB (04 Nov, 2026)', 'LB__04_Nov__2026_', 'LB (04 Nov, 2026) (1)'

try:                                        # crisp text on Windows (no blurry scaling)
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

root = tk.Tk(); root.title('Slip Kiosk - Servis Tyres'); root.configure(bg=BG)
root.option_add('*TCombobox*Listbox.font', FN)


def setup_style():
    s = ttk.Style()
    try: s.theme_use('clam')
    except tk.TclError: pass
    s.configure('.', font=FN, background=BG, foreground=INK, focuscolor=BG)
    # tabs: soft pills, the active one is solid navy
    s.configure('TNotebook', background=BG, borderwidth=0, bordercolor=BG, lightcolor=BG, darkcolor=BG, tabmargins=(16, 10, 16, 0))
    s.configure('TNotebook.Tab', font=('Segoe UI', 11, 'bold'), padding=(30, 11), background='#f1f1f1', foreground=MUTED,
                bordercolor=BG, lightcolor=BG, darkcolor=BG, borderwidth=1)
    s.map('TNotebook.Tab', background=[('selected', PRIMARY), ('active', '#e2e2e2')], foreground=[('selected', 'white')],
          bordercolor=[('selected', PRIMARY)], lightcolor=[('selected', PRIMARY)], darkcolor=[('selected', PRIMARY)],
          expand=[('selected', (0, 0, 0, 0))], padding=[('selected', (30, 11))])
    # buttons: default (outlined), Primary (navy), Ghost (for the dark header)
    s.configure('TButton', font=('Segoe UI', 10, 'bold'), padding=(16, 8), background='#f2f2f2', foreground=NAVY, bordercolor='#d0d0d0',
                lightcolor='#f2f2f2', darkcolor='#f2f2f2', relief='flat', focusthickness=0)
    s.map('TButton', background=[('pressed', '#e2e2e2'), ('active', '#e2e2e2')], foreground=[('disabled', '#a8a8a8')])
    s.configure('Primary.TButton', background=PRIMARY, foreground='white', bordercolor=PRIMARY, lightcolor=PRIMARY, darkcolor=PRIMARY)
    s.map('Primary.TButton', background=[('pressed', '#82030a'), ('active', '#a3040c')], foreground=[('disabled', '#f7a8ae')])
    s.configure('Ghost.TButton', background='#f2f2f2', foreground='#111111', bordercolor='#d0d0d0', lightcolor='#f2f2f2', darkcolor='#f2f2f2')
    s.map('Ghost.TButton', background=[('pressed', '#d8d8d8'), ('active', '#e2e2e2')])
    # inputs
    for w in ('TEntry', 'TCombobox'):
        s.configure(w, padding=(8, 6), fieldbackground='white', bordercolor=LINE, lightcolor=LINE, darkcolor=LINE, insertcolor=PRIMARY)
        s.map(w, bordercolor=[('focus', PRIMARY)], lightcolor=[('focus', PRIMARY)], darkcolor=[('focus', PRIMARY)])
    s.configure('TCombobox', background='white', arrowcolor=NAVY, selectbackground='white', selectforeground=INK)
    s.map('TCombobox', fieldbackground=[('readonly', 'white')], selectbackground=[('readonly', 'white')], selectforeground=[('readonly', INK)])
    for w in ('Card.TRadiobutton', 'Card.TCheckbutton'):
        s.configure(w, background='white', foreground=INK, font=FN, indicatorbackground='white', indicatorforeground=NAVY, focuscolor='white', indicatorsize=18, indicatormargin=(0, 0, 8, 0))
        s.map(w, background=[('active', 'white')], indicatorbackground=[('selected', PRIMARY), ('!selected', 'white')],
              indicatorforeground=[('selected', 'white')])
    s.configure('Vertical.TScrollbar', background='#c9c9c9', troughcolor=BG, bordercolor=BG, lightcolor='#c9c9c9', darkcolor='#c9c9c9',
                arrowcolor=NAVY, gripcount=0, arrowsize=16)
    s.map('Vertical.TScrollbar', background=[('active', '#a8a8a8')])


setup_style()


def make_card(parent, title=None, px=18, py=14):
    """White panel with a 1px border. Returns (outer, body): place `outer`, fill `body`."""
    outer = tk.Frame(parent, bg=LINE)
    inner = tk.Frame(outer, bg='white'); inner.pack(fill='both', expand=True, padx=1, pady=1)
    if title:
        tk.Label(inner, text=title, font=('Segoe UI', 11, 'bold'), fg=NAVY, bg='white').pack(anchor='w', padx=px, pady=(py, 0))
        tk.Frame(inner, bg=LINE, height=1).pack(fill='x', padx=px, pady=(8, 0))
    body = tk.Frame(inner, bg='white'); body.pack(fill='both', expand=True, padx=px, pady=py)
    return outer, body


def hover(w, normal, over):
    w.bind('<Enter>', lambda e: str(w['state']) != 'disabled' and w.config(bg=over))
    w.bind('<Leave>', lambda e: w.config(bg=normal))


def center(win):
    win.update_idletasks()
    win.geometry(f'+{(win.winfo_screenwidth() - win.winfo_width()) // 2}+{(win.winfo_screenheight() - win.winfo_height()) // 3}')
    win.attributes('-topmost', True); win.lift(); win.focus_force(); win.grab_set()


def dialog(title):
    win = tk.Toplevel(root); win.title(title); win.configure(bg='white'); win.resizable(False, False)
    tk.Frame(win, bg=RED, height=2).pack(fill='x')
    body = tk.Frame(win, bg='white', padx=40, pady=28); body.pack()
    return win, body

# ---- login (password only). First run: set password + confirm. Forgot it: type "Block HR" as the password to set a new one.
RESET_WORD = 'block hr'
SHARED_PW = None  # PACK_PW   <- pack.py puts the password from password.json (repo) here, so every PC uses the same password


def _active_pw():
    """Password record in use: the shared one from the link; a local one only if no shared password exists
    or it was set on this PC while the current shared one was active (it stops working once the repo password changes)."""
    loc = cfg.get('pw') if isinstance(cfg.get('pw'), dict) and cfg['pw'].get('hash') else None
    if SHARED_PW and isinstance(SHARED_PW, dict) and SHARED_PW.get('hash'):
        return loc if loc and loc.get('base') == SHARED_PW['hash'] else SHARED_PW
    return loc


def _hash(pw, salt):
    return hashlib.pbkdf2_hmac('sha256', pw.encode('utf-8'), bytes.fromhex(salt), 200000).hex()


def _save_pw(pw):
    salt = secrets.token_hex(16)
    cfg['pw'] = {'salt': salt, 'hash': _hash(pw, salt)}        # only a salted hash is stored, never the password itself
    if SHARED_PW and SHARED_PW.get('hash'): cfg['pw']['base'] = SHARED_PW['hash']
    json.dump(cfg, open(CFG, 'w'))
    return {'salt': cfg['pw']['salt'], 'hash': cfg['pw']['hash']}


def show_shared_pw(rec):
    """After a password is set: show the text to save as password.json in the code repo -> all PCs then use this password."""
    win, body = dialog('Use this password on all PCs')
    txt = json.dumps(rec)
    tk.Label(body, text='Password saved on this PC', font=('Segoe UI', 16, 'bold'), fg=NAVY, bg='white').pack(anchor='w')
    tk.Label(body, text='To use the same password on every PC, with no setup on the other PCs:', fg=MUTED, bg='white', font=FN,
             justify='left', wraplength=500).pack(anchor='w', pady=(4, 12))
    for i, t in enumerate(['Click Copy below.', 'In the code repo create or replace  password.json  and paste it.',
                           'Commit and wait for "Publish code to Pages" to turn green.'], 1):
        row = tk.Frame(body, bg='white'); row.pack(anchor='w', fill='x', pady=3)
        tk.Label(row, text=str(i), font=('Segoe UI', 9, 'bold'), fg='white', bg=PRIMARY, width=2).pack(side='left', padx=(0, 12))
        tk.Label(row, text=t, bg='white', fg=INK, font=FN, justify='left', wraplength=460).pack(side='left')
    tk.Label(body, text='Other PCs pick it up the next time the exe starts.', fg=MUTED, bg='white', font=FN).pack(anchor='w', pady=(10, 12))
    e = ttk.Entry(body, width=64, font=('Consolas', 9)); e.insert(0, txt); e.pack(fill='x'); e.state(['readonly'])

    def copy():
        root.clipboard_clear(); root.clipboard_append(txt); root.update()
        cp.config(text='Copied')
    bt = tk.Frame(body, bg='white'); bt.pack(anchor='e', pady=(16, 0))
    cp = ttk.Button(bt, text='Copy', style='Primary.TButton', command=copy); cp.pack(side='left', padx=(0, 8))
    ttk.Button(bt, text='Close', command=win.destroy).pack(side='left')
    center(win)
    root.wait_window(win)


def _check_pw(pw):
    try:
        r = _active_pw()
        return hmac.compare_digest(_hash(pw, r['salt']), r['hash'])
    except Exception:
        return False


def login():
    win, body = dialog('Slip Kiosk - Login')
    ok, mode = [False], ['login' if _active_pw() else 'setup']
    p1, p2, msg = tk.StringVar(), tk.StringVar(), tk.StringVar()
    try: win.logo = tk.PhotoImage(data=LOGO_B64, master=win)       # same Servis Tyres logo as the main window
    except Exception: win.logo = None

    def build():
        for w in body.winfo_children(): w.destroy()
        p1.set(''); p2.set('')
        setup = mode[0] == 'setup'
        if win.logo: tk.Label(body, image=win.logo, bg='white').pack(pady=(0, 10 if setup else 20))
        if setup:                                                   # login screen: logo + password only, no extra heading
            tk.Label(body, text='Create password', font=('Segoe UI', 19, 'bold'), fg=NAVY, bg='white').pack()
            tk.Label(body, text='It protects the settings and the exit button', font=FN, fg=MUTED, bg='white').pack(pady=(2, 16))
        tk.Label(body, text='Password', bg='white', font=FN, fg=MUTED).pack(anchor='w')
        e1 = ttk.Entry(body, textvariable=p1, show='\u2022', width=30, font=('Segoe UI', 12)); e1.pack(fill='x', pady=(3, 10))
        if setup:
            tk.Label(body, text='Confirm password', bg='white', font=FN, fg=MUTED).pack(anchor='w')
            ttk.Entry(body, textvariable=p2, show='\u2022', width=30, font=('Segoe UI', 12)).pack(fill='x', pady=(3, 10))
        tk.Label(body, textvariable=msg, fg=RED, bg='white', font=FN, wraplength=300).pack()
        ttk.Button(body, text='Save password' if setup else 'Login', style='Primary.TButton', command=submit).pack(fill='x', pady=(10, 0))
        e1.focus_set()

    def submit(event=None):
        pw = p1.get()
        if mode[0] == 'setup':
            if len(pw) < 4: msg.set('Password must be at least 4 characters'); return
            if pw.strip().casefold() == RESET_WORD: msg.set('This word cannot be used as a password'); return
            if pw != p2.get(): msg.set('Passwords do not match'); return
            rec = _save_pw(pw); ok[0] = True; win.destroy(); show_shared_pw(rec)
        elif pw.strip().casefold() == RESET_WORD:
            mode[0] = 'setup'; build(); msg.set('Set a new password')
        elif _check_pw(pw):
            ok[0] = True; win.destroy()
        else:
            msg.set('Wrong password'); p1.set('')

    build()
    win.bind('<Return>', submit)
    center(win)
    root.wait_window(win)
    return ok[0]


root.withdraw()
if not login():
    root.destroy(); sys.exit(0)
root.deiconify()
_sw, _sh = root.winfo_screenwidth(), root.winfo_screenheight()
_w, _h = min(1240, int(_sw * 0.94)), min(820, int(_sh * 0.92))
root.geometry(f'{_w}x{_h}+{(_sw - _w) // 2}+{max(0, (_sh - _h) // 3)}'); root.minsize(min(980, _w), min(640, _h)); root.after(300, root.focus_force)
root.protocol('WM_DELETE_WINDOW', lambda: root.iconify())   # X button minimizes to taskbar, never closes
v = {k: tk.StringVar(value=str(cfg[k])) for k in ('device_ip', 'device_port', 'comm_key', 'printer_ip', 'paper', 'days', 'printer_name', 'mode', 'source_dir', 'sync_min')}
auto, plain = tk.BooleanVar(value=cfg['autorun']), tk.BooleanVar(value=cfg['plain'])

# ---- header: navy bar, logo badge, title, status pill
hd = tk.Frame(root, bg=HEAD); hd.pack(fill='x')
badge = tk.Frame(hd, bg='white'); badge.pack(side='left', padx=(18, 14), pady=10)
try:
    logo = tk.PhotoImage(data=LOGO_B64)
    try:                                                              # smooth, smaller logo for the header (falls back to the original)
        from PIL import ImageTk
        logo = ImageTk.PhotoImage(Image.open(io.BytesIO(base64.b64decode(LOGO_B64))).convert('RGBA').resize((57, 54), Image.LANCZOS))
    except Exception:
        pass
    tk.Label(badge, image=logo, bg='white').pack(padx=6, pady=4)
except Exception:
    pass
tb = tk.Frame(hd, bg=HEAD); tb.pack(side='left')
tk.Label(tb, text='Attendance Slip Kiosk', font=('Segoe UI', 18, 'bold'), fg='#111111', bg=HEAD).pack(anchor='w')
tk.Label(tb, text='Servis Tyres  |  Attendance and leave slips', font=('Segoe UI', 9), fg='#6b6b6b', bg=HEAD).pack(anchor='w')
pill = tk.Label(hd, text='\u25cf  STOPPED', font=('Segoe UI', 10, 'bold'), fg='#111111', bg='#eeeeee', padx=16, pady=6); pill.pack(side='right', padx=(10, 18))
ttk.Button(hd, text='Exit', style='Ghost.TButton', command=lambda: request_exit()).pack(side='right')
tread = tk.Canvas(root, height=4, bg=PRIMARY, highlightthickness=0, bd=0); tread.pack(fill='x')      # tyre-tread strip


def _tread(e=None):
    tread.delete('all')
    pass                                                      # plain red line, no zigzag


tread.bind('<Configure>', _tread)

# ---- tabs: Dashboard (touch keypad + slip preview) | Connectivity (machine + printer) | Data (WH / LB reports)
nb = ttk.Notebook(root); nb.pack(fill='both', expand=True, padx=8, pady=(4, 8))
tab_dash, tab_conn, tab_data = (tk.Frame(nb, bg=BG) for _ in range(3))
nb.add(tab_dash, text='Dashboard'); nb.add(tab_conn, text='Connectivity'); nb.add(tab_data, text='Data')

# ---- overview cards
sv = {k: tk.StringVar(value='-') for k in ('mach', 'mach_state', 'prn', 'wh', 'lb', 'emp', 'sync', 'watch', 'slips', 'last')}
cardlbl = {}


def card(parent, title, keys, col, wrap=200):
    outer, body = make_card(parent, title, px=16, py=10)
    outer.grid(row=0, column=col, sticky='nsew', padx=6); parent.columnconfigure(col, weight=1, uniform='c')
    for k in keys:
        cardlbl[k] = tk.Label(body, textvariable=sv[k], bg='white', fg=INK, font=('Segoe UI', 10), anchor='w', justify='left', wraplength=wrap)
        cardlbl[k].pack(fill='x', pady=1)


cards_c = tk.Frame(tab_conn, bg=BG); cards_c.pack(fill='x', padx=10, pady=(12, 8))
card(cards_c, 'Machine', ['mach', 'mach_state'], 0); card(cards_c, 'Printer', ['prn'], 1); card(cards_c, 'Activity', ['slips', 'last'], 2)
cards_d = tk.Frame(tab_data, bg=BG); cards_d.pack(fill='x', padx=10, pady=(12, 8))
card(cards_d, 'Reports', ['wh', 'lb', 'emp', 'watch', 'sync'], 0, wrap=900)


# ---- settings
def printers():
    try:
        import win32print
        return sorted(p[2] for p in win32print.EnumPrinters(2 | 4))     # every printer installed in Windows
    except Exception:
        try:
            import subprocess
            out = subprocess.run(['powershell', '-NoProfile', '-Command', '(Get-Printer).Name'], capture_output=True,
                                 text=True, timeout=15, creationflags=0x08000000).stdout
            return sorted(x.strip() for x in out.splitlines() if x.strip())
        except Exception:
            return []


def box(parent, title, col):
    outer, body = make_card(parent, title)
    outer.grid(row=0, column=col, sticky='nsew', padx=6); parent.columnconfigure(col, weight=1, uniform='s'); return body


def field(parent, r, text, var, width=20):
    tk.Label(parent, text=text, bg='white', fg=MUTED, font=FN).grid(row=r, column=0, sticky='w', padx=(0, 16), pady=5)
    ttk.Entry(parent, textvariable=var, width=width).grid(row=r, column=1, sticky='ew', pady=5)


st = tk.Frame(tab_conn, bg=BG); st.pack(fill='x', padx=10)
mf, pf = box(st, 'Machine and slip', 0), box(st, 'Printer connection (tick the one to use)', 1)
for i, (t, k) in enumerate([('Machine IP', 'device_ip'), ('Machine port', 'device_port'), ('Comm Key', 'comm_key'),
                            ('Paper width (58/80 mm)', 'paper'), ('Days shown on slip', 'days')]):
    field(mf, i, t, v[k])
mf.columnconfigure(1, weight=1)
pf.columnconfigure(1, weight=1)
ttk.Radiobutton(pf, text='Network printer (IP)', variable=v['mode'], value='network', style='Card.TRadiobutton').grid(row=0, column=0, sticky='w', pady=5)
ttk.Entry(pf, textvariable=v['printer_ip'], width=22).grid(row=0, column=1, sticky='ew', padx=(14, 0), pady=5)
ttk.Radiobutton(pf, text='USB / Windows printer', variable=v['mode'], value='usb', style='Card.TRadiobutton').grid(row=1, column=0, sticky='w', pady=5)
cb = ttk.Combobox(pf, textvariable=v['printer_name'], values=printers(), width=30, state='readonly'); cb.grid(row=1, column=1, sticky='ew', padx=(14, 0), pady=5)
ttk.Button(pf, text='Refresh', command=lambda: cb.config(values=printers())).grid(row=1, column=2, padx=(8, 0))
def open_queue():
    n = v['printer_name'].get().strip()
    if not n: messagebox.showinfo('Print queue', 'Select a USB / Windows printer first'); return
    import subprocess
    subprocess.Popen(['rundll32', 'printui.dll,PrintUIEntry', '/o', '/n', n])


ttk.Checkbutton(pf, text='Office / laser / inkjet printer (print as normal text)', variable=plain, style='Card.TCheckbutton').grid(row=2, column=0, columnspan=2, sticky='w', pady=(8, 2))
ttk.Button(pf, text='Print queue', command=open_queue).grid(row=2, column=2, padx=(8, 0), pady=(8, 2))
ttk.Checkbutton(pf, text='Start automatically with Windows', variable=auto, style='Card.TCheckbutton').grid(row=3, column=0, columnspan=2, sticky='w', pady=2)


# ---- Data tab: linked folder
af_o, af = make_card(tab_data, 'Reports auto-update')
af_o.pack(fill='x', padx=16, pady=(0, 8))
tk.Label(af, text='Optional second folder to watch (the reports folder next to the exe is always watched). File name must contain WH or LB.', bg='white', fg=MUTED, font=FN).pack(anchor='w', pady=(0, 10))
row_f = tk.Frame(af, bg='white'); row_f.pack(fill='x')
tk.Label(row_f, text='Folder', bg='white', fg=MUTED, font=FN).pack(side='left', padx=(0, 10))
ttk.Entry(row_f, textvariable=v['source_dir']).pack(side='left', fill='x', expand=True)
ttk.Button(row_f, text='Browse', command=lambda: v['source_dir'].set(filedialog.askdirectory() or v['source_dir'].get())).pack(side='left', padx=(8, 22))
tk.Label(row_f, text='Check every', bg='white', fg=MUTED, font=FN).pack(side='left')
ttk.Entry(row_f, textvariable=v['sync_min'], width=5).pack(side='left', padx=6)
tk.Label(row_f, text='min', bg='white', fg=MUTED, font=FN).pack(side='left')
ttk.Button(row_f, text='Check now', style='Primary.TButton', command=lambda: safe_apply() and threading.Thread(target=sb.sync_reports, daemon=True).start()).pack(side='left', padx=(16, 0))


def apply():
    for k in v: cfg[k] = v[k].get().strip()
    cfg['autorun'], cfg['plain'] = auto.get(), plain.get()
    for k in ('device_port', 'comm_key', 'days', 'sync_min'):
        if not cfg[k].isdigit(): raise ValueError(f'{k.replace("_", " ")} must be a number')
    if cfg['mode'] == 'usb' and not cfg['printer_name']: raise ValueError('Select a USB / Windows printer')
    sb.DEVICE_IP, sb.DEVICE_PORT, sb.COMM_KEY = cfg['device_ip'], int(cfg['device_port']), int(cfg['comm_key'])
    sb.PRINTER_IP, sb.PRINTER_NAME = cfg['printer_ip'], (cfg['printer_name'] if cfg['mode'] == 'usb' else '')
    sb.SOURCE_DIR, sb.SYNC_MIN = cfg['source_dir'], max(1, int(cfg['sync_min']))
    sb.PRINT_MODE = 'text' if cfg['plain'] else 'raw'
    sb.COLS, sb.DAYS = (32 if cfg['paper'] == '58' else 40), int(cfg['days'])
    json.dump(cfg, open(CFG, 'w'))
    try:
        if cfg['autorun']:
            cmd = f'"{sys.executable}"' if getattr(sys, 'frozen', False) else f'pythonw "{os.path.abspath(__file__)}"'
            open(BAT, 'w').write(f'@echo off\nstart "" {cmd}\n')
        elif os.path.exists(BAT):
            os.remove(BAT)
    except OSError:
        pass


def safe_apply():
    try: apply(); return True
    except ValueError as e: messagebox.showerror('Check settings', str(e)); return False


th = None
def start():
    global th
    if not safe_apply() or (th and th.is_alive()): return
    sb.STOP.clear(); th = threading.Thread(target=sb.live, daemon=True); th.start()


def stop(): sb.STOP.set(); sb.STATS['connected'] = False


load_busy, load_btns = [False], []


def load_report(kind):                     # kind: 'WH' (attendance) or 'LB' (leave balance); accepts the raw HR export (.xls = HTML), real .xls or .xlsx
    f = filedialog.askopenfilename(title=f'Select {kind} report', filetypes=[('Report files', '*.xls *.xlsx *.htm *.html')])
    if not f: return
    other = file_kind(os.path.basename(f))
    if other and other != kind:
        messagebox.showerror('Wrong file', f'This file name says {other}, but you pressed "Load {kind} report".'); return
    d = file_date(f); cur = _loaded_date(kind)
    if cur and d < cur:
        messagebox.showerror('Older report', f'The loaded {kind} report is dated {cur:%d %b %Y}.\nThis file ({d:%d %b %Y}) is older and will not be used.'); return
    if load_busy[0]: return
    load_busy[0] = True
    for b in load_btns: b.config(state='disabled')
    load_btns[0 if kind == 'WH' else 1].config(text='Loading, please wait...')

    def done(err=None):                                   # back on the window thread: restore buttons, show any error
        load_busy[0] = False
        for b, t in zip(load_btns, ('Load WH report', 'Load LB report')): b.config(state='normal', text=t)
        if err: messagebox.showerror('Could not read file', f'Please check the file.\n{err}')

    def work():                                           # heavy part (convert, check, load) runs in the background so the window never hangs
        try:
            msg, _ = ingest(f, kind, d); _log(msg)
        except Exception as e:
            _log(f'Could not load {os.path.basename(f)}: {e}')
            root.after(0, lambda e=e: done(e)); return
        root.after(0, done)

    threading.Thread(target=work, daemon=True).start()


# ---- system tray icon (Open = restore window). Exit stays on the password-protected button below.
tray_q = queue.Queue()
tray_icon = None


def _tray_image():
    return Image.open(io.BytesIO(base64.b64decode(LOGO_B64)))


def _tray_open(icon=None, item=None): tray_q.put('open')
def _tray_exit(icon=None, item=None): tray_q.put('exit')


def start_tray():
    global tray_icon
    menu = pystray.Menu(pystray.MenuItem('Open Slip Kiosk', _tray_open, default=True), pystray.MenuItem('Exit', _tray_exit))
    tray_icon = pystray.Icon('slip_kiosk', _tray_image(), 'Slip Kiosk - Servis Tyres', menu)
    threading.Thread(target=tray_icon.run, daemon=True).start()


# ---- password-protected exit (Exit button below; type the right password to close completely)
def confirm_exit_password(title='Exit Slip Kiosk', prompt='Enter password to exit completely', btn='Exit'):
    win, body = dialog(title)
    pw, msg, result = tk.StringVar(), tk.StringVar(), [False]
    tk.Label(body, text=prompt, font=('Segoe UI', 13, 'bold'), fg=NAVY, bg='white').pack(pady=(0, 12))
    e = ttk.Entry(body, textvariable=pw, show='\u2022', width=28, font=('Segoe UI', 12)); e.pack(fill='x')
    tk.Label(body, textvariable=msg, fg=RED, bg='white', font=FN).pack(pady=(6, 0))

    def submit(event=None):
        if _check_pw(pw.get()): result[0] = True; win.destroy()
        else: msg.set('Wrong password'); pw.set('')

    ttk.Button(body, text=btn, style='Primary.TButton', command=submit).pack(fill='x', pady=(10, 6))
    ttk.Button(body, text='Cancel', command=win.destroy).pack(fill='x')
    win.bind('<Return>', submit)
    center(win)
    e.focus_set()
    root.wait_window(win)
    return result[0]


def request_exit():
    root.deiconify(); root.lift(); root.focus_force()    # show window so the password box isn't hidden
    if confirm_exit_password():
        sb.STOP.set()
        try: tray_icon.stop()
        except Exception: pass
        root.destroy()
        os._exit(0)


# ---- Dashboard tab: touch keypad (left) + slip preview with Print (right)
dash_q = queue.Queue()
entered, pstat, shown = tk.StringVar(), tk.StringVar(), tk.StringVar()
fresh, cur_slip = [False], [None]                      # fresh = next digit starts a new ID; cur_slip = slip text on screen
tab_dash.columnconfigure(0, weight=2, uniform='d'); tab_dash.columnconfigure(1, weight=3, uniform='d'); tab_dash.rowconfigure(0, weight=1)
left_o, left = make_card(tab_dash, px=24, py=20)
right_o, right = make_card(tab_dash, px=18, py=16)
left_o.grid(row=0, column=0, sticky='nsew', padx=(10, 6), pady=8); right_o.grid(row=0, column=1, sticky='nsew', padx=(6, 10), pady=8)

top_l = tk.Frame(left, bg='white'); top_l.pack(fill='x', pady=(0, 10))                     # logo + heading on top of the keypad panel
try:
    try:
        from PIL import ImageTk
        logo_big = ImageTk.PhotoImage(Image.open(io.BytesIO(base64.b64decode(LOGO_B64))).convert('RGBA').resize((76, 72), Image.LANCZOS))
    except Exception:
        logo_big = tk.PhotoImage(data=LOGO_B64)
    tk.Label(top_l, image=logo_big, bg='white').pack(side='left', padx=(0, 16))
except Exception:
    pass
txt_l = tk.Frame(top_l, bg='white'); txt_l.pack(side='left')
tk.Label(txt_l, text='Employee ID', font=('Segoe UI', 13, 'bold'), fg=NAVY, bg='white').pack(anchor='w')
tk.Label(txt_l, text='Type or tap your ID, then press Enter', font=FN, fg=MUTED, bg='white').pack(anchor='w')
disp_o = tk.Frame(left, bg=LINE); disp_o.pack(fill='x', pady=(0, 14))
disp = tk.Label(disp_o, textvariable=shown, font=('Segoe UI', 34, 'bold'), fg=NAVY, bg='#f6f6f6', anchor='center')
disp.pack(fill='x', padx=1, pady=1, ipady=10)


def _show_id(*_):
    s = entered.get(); shown.set(s or 'ID'); disp.config(fg=NAVY if s else '#bdbdbd'); disp_o.config(bg=PRIMARY if s else LINE)    # grey placeholder when empty; thin red outline while typing


entered.trace_add('write', _show_id); _show_id()
pad = tk.Frame(left, bg='white', height=520); pad.pack(fill='x'); pad.grid_propagate(False)      # keypad: a bit smaller, never taller than the panel allows


def fit_pad(e=None):                                  # keypad height = what is left in the panel, capped so the buttons are a little smaller
    free = left.winfo_height() - top_l.winfo_reqheight() - disp_o.winfo_reqheight() - 10 - 14 - 6
    if left.winfo_height() > 100: pad.config(height=max(200, min(520, free)))


left.bind('<Configure>', fit_pad)


btns, _anim = {}, {}


def _mix(c1, c2, t):                                  # colour blend, t = 0 -> c1, t = 1 -> c2
    a, b = [int(c1[i:i + 2], 16) for i in (1, 3, 5)], [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return '#%02x%02x%02x' % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def fade_btn(t, steps=6, ms=20):                      # pressed colour -> normal colour, smoothly
    b, look = btns[t]
    if _anim.get(t): root.after_cancel(_anim[t])
    def step(i=0):
        over = root.winfo_containing(root.winfo_pointerx(), root.winfo_pointery()) is b
        end_bg = look['hv'] if over else look['bg']
        k = (i + 1) / steps
        b.config(bg=_mix(look['pr'], end_bg, k), fg=_mix(look['pf'], look['fg'], k))
        _anim[t] = root.after(ms, step, i + 1) if i + 1 < steps else None
    step()


def flash(t):                                         # used for the physical keyboard: same press effect as a tap
    if t not in btns: return
    b, look = btns[t]
    b.config(bg=look['pr'], fg=look['pf']); root.after(70, lambda: fade_btn(t))


def key(d):
    if fresh[0]: entered.set(''); fresh[0] = False
    if len(entered.get()) < 12: entered.set(entered.get() + d)


shown_slip, fit_size = [None], [None]


def fit_slip():                                       # auto-size the slip font to the space on THIS screen: the whole slip shows, no scrolling
    text = shown_slip[0]
    if not text: return
    from tkinter import font as tkfont
    desk.update_idletasks()
    lines = text.rstrip('\n').split('\n')
    n, longest = len(lines), max(len(l) for l in lines)
    avail_h = desk.winfo_height() - 16 - 2 - 20 - 6          # desk minus paper margins, border, text padding, safety
    avail_w = desk.winfo_width() - 40 - 2 - 28
    if avail_h < 80 or avail_w < 80: return                   # window not laid out yet; the <Configure> event calls us again
    px = 7
    for cand in range(20, 5, -1):                             # biggest pixel size that fits both height and width
        f = tkfont.Font(family='Courier New', size=-cand)
        if f.metrics('linespace') * n <= avail_h and f.measure('0') * longest <= avail_w: px = cand; break
    if fit_size[0] != px:
        fit_size[0] = px; pv.config(font=('Courier New', -px))
    pv.config(width=longest + 1, height=n)                   # height = number of slip lines, so the whole slip is visible (preview only, print unchanged)


def show(text, hint=False):                           # hint=True: big centred grey message instead of a slip
    shown_slip[0] = None if hint else text
    pv.config(state='normal'); pv.delete('1.0', 'end')
    if hint: fit_size[0] = None; pv.config(font=('Courier New', 12), width=42, height=24)
    pv.insert('end', text, 'hint' if hint else 'slip'); pv.config(state='disabled'); pv.yview_moveto(0)
    if not hint: fit_slip()


def clear():
    entered.set(''); fresh[0] = False; cur_slip[0] = None; pstat.set(''); show('\n\n\n\nSlip Preview', True)


def enter():
    uid = entered.get().strip()
    if not uid: return
    fresh[0] = True; pstat.set('')
    if not safe_apply(): return
    if sb.STATS['loading']: cur_slip[0] = None; show('\n\n\nReports are loading,\ntry again in a moment', True); return
    text = sb.slip(uid, datetime.now())
    if not text: cur_slip[0] = None; show(f'\n\n\nID {uid}\nwas not found in the reports', True); return
    cur_slip[0] = text; show(text)


def print_now():
    t = cur_slip[0]
    if not t: messagebox.showinfo('Print', 'Enter an ID and press Enter to see the slip first'); return
    prt.config(state='disabled'); pstat.set('Printing...'); pstat_lbl.config(fg='#555')

    def work():
        try: sb.print_slip(t); dash_q.put(('ok', t))
        except Exception as e: dash_q.put(('err', str(e)))
    threading.Thread(target=work, daemon=True).start()


KP = [['7', '8', '9'], ['4', '5', '6'], ['1', '2', '3'], ['Clear', '0', 'Enter']]
for r, row in enumerate(KP):
    pad.rowconfigure(r, weight=1, uniform='k')
    for c, t in enumerate(row):
        pad.columnconfigure(c, weight=1, uniform='k')
        cmd = clear if t == 'Clear' else enter if t == 'Enter' else (lambda d=t: key(d))
        look = {'Clear': dict(fg=INK, bg='#e8e8e8', hv='#dcdcdc', pr='#c9c9c9', pf=INK),
                'Enter': dict(fg='white', bg=PRIMARY, hv=PRIMARY_D, pr='#82030a', pf='white')}.get(t, dict(fg=NAVY, bg='#f4f4f4', hv='#ebebeb', pr='#d2d2d2', pf=NAVY))
        b = tk.Button(pad, text=t, command=cmd, font=('Segoe UI', 24 if len(t) == 1 else 17, 'bold'), relief='flat', bd=0, fg=look['fg'],
                      bg=look['bg'], activebackground=look['pr'], activeforeground=look['pf'], takefocus=0, cursor='hand2')
        b.grid(row=r, column=c, sticky='nsew', padx=4, pady=4)
        hover(b, look['bg'], look['hv'])
        btns[t] = (b, look)
        b.bind('<ButtonRelease-1>', lambda e, t=t: root.after(40, fade_btn, t), add='+')     # tap: red flash that fades out

top = tk.Frame(right, bg='white'); top.pack(fill='x', pady=(0, 8))
tk.Label(top, text='Slip preview', font=('Segoe UI', 13, 'bold'), fg=NAVY, bg='white').pack(side='left')
pstat_lbl = tk.Label(top, textvariable=pstat, font=('Segoe UI', 12, 'bold'), bg='white', fg='#555'); pstat_lbl.pack(side='left', padx=18)
prt = tk.Button(top, text='Print slip', command=print_now, font=('Segoe UI', 18, 'bold'), fg='white', bg=PRIMARY, activebackground=PRIMARY_D,
                activeforeground='white', disabledforeground='#f7a8ae', relief='flat', bd=0, padx=30, pady=6, takefocus=0, cursor='hand2')
prt.pack(side='right'); hover(prt, PRIMARY, PRIMARY_D)
desk = tk.Frame(right, bg='#f2f2f2'); desk.pack(fill='both', expand=True)             # grey desk with the slip as a sheet of paper
paper = tk.Frame(desk, bg=LINE); paper.pack(fill='y', expand=True, pady=8)
pw_ = tk.Frame(paper, bg='white'); pw_.pack(fill='both', expand=True, padx=1, pady=1)
sc = ttk.Scrollbar(pw_)                                  # kept only as a hook; never shown (the slip is auto-fitted instead)
pv = tk.Text(pw_, font=('Courier New', 12), width=42, wrap='none', bg='white', fg='#000000', relief='flat', bd=0, padx=14, pady=10, highlightthickness=0,
             yscrollcommand=sc.set, cursor='arrow', takefocus=0)
pv.pack(side='left', fill='both', expand=True)
desk.bind('<Configure>', lambda e: root.after_idle(fit_slip))   # window resized / different screen -> refit
pv.tag_configure('hint', font=('Segoe UI', 20, 'bold'), foreground='#9a9a9a', justify='center'); pv.tag_configure('slip', justify='left', foreground='#000000')
clear()


def on_key(e):                                         # physical keyboard also works on the Dashboard tab
    try:
        if nb.select() != str(tab_dash) or isinstance(root.focus_get(), (tk.Entry, ttk.Entry, ttk.Combobox)): return
    except Exception:
        return
    if e.char and e.char.isdigit(): flash(e.char); key(e.char)
    elif e.keysym == 'BackSpace': entered.set(entered.get()[:-1]); fresh[0] = False
    elif e.keysym in ('Return', 'KP_Enter'): flash('Enter'); enter()
    elif e.keysym == 'Escape': flash('Clear'); clear()


root.bind('<Key>', on_key)
sb.SLIP_HOOK = lambda uid, text, state, err: dash_q.put(('punch', (uid, text, state, err)))

# ---- Connectivity and Data tabs open only after typing the login password (Dashboard is always open)
unlocked = [False]


def tab_click(e):
    try: i = nb.index(f'@{e.x},{e.y}')
    except tk.TclError: return
    if nb.tabs()[i] == str(tab_dash): return                    # Dashboard: normal
    if not unlocked[0]:
        if not confirm_exit_password('Password required', 'Enter password to open this tab', 'Open'): return 'break'
        unlocked[0] = True
    nb.select(i); return 'break'


def tab_changed(e=None):
    if nb.select() == str(tab_dash): unlocked[0] = False        # leaving the admin tabs locks them again
    elif not unlocked[0]: nb.select(tab_dash)                   # e.g. Ctrl+Tab without the password


nb.bind('<Button-1>', tab_click); nb.bind('<<NotebookTabChanged>>', tab_changed)

# ---- Connectivity tab buttons + live log | Data tab buttons
bar = tk.Frame(tab_conn, bg=BG); bar.pack(fill='x', padx=16, pady=12)
ttk.Button(bar, text='Save + Start', style='Primary.TButton', command=start).pack(side='left')
ttk.Button(bar, text='Stop', command=stop).pack(side='left', padx=8)
log_o, log_b = make_card(tab_conn, 'Live log', py=10)
log_o.pack(fill='both', expand=True, padx=16, pady=(0, 14))
lsc = ttk.Scrollbar(log_b); lsc.pack(side='right', fill='y')
log = tk.Text(log_b, height=8, font=('Consolas', 9), bg='#111111', fg='#f2f2f2', insertbackground=PRIMARY, relief='flat', bd=0, padx=10, pady=8,
              highlightthickness=0, wrap='word', yscrollcommand=lsc.set)
log.pack(side='left', fill='both', expand=True); lsc.config(command=log.yview)
bd_o, bar_d = make_card(tab_data, 'Manual upload')
bd_o.pack(fill='x', padx=16, pady=(0, 8))
tk.Label(bar_d, text='Normally not needed: just copy the WH / LB files into the reports folder. Or pick a file here (raw .xls export, .xls or .xlsx).', bg='white', fg=MUTED, font=FN).pack(anchor='w', pady=(0, 10))
btn_row = tk.Frame(bar_d, bg='white'); btn_row.pack(anchor='w')
for t, c in [('Load WH report', lambda: load_report('WH')), ('Load LB report', lambda: load_report('LB'))]:
    load_btns.append(ttk.Button(btn_row, text=t, style='Primary.TButton', command=c)); load_btns[-1].pack(side='left', padx=(0, 8))


def poll():
    while not dash_q.empty():
        kind, info = dash_q.get(); prt.config(state='normal')
        if kind == 'ok':
            sb.STATS['printer'] = 'OK (manual print)'
            if cur_slip[0] == info: clear()                     # printed -> ID and preview cleared, ready for the next employee
            pstat_lbl.config(fg=INK); pstat.set('Printed'); root.after(3000, lambda: pstat.get() == 'Printed' and pstat.set(''))
        elif kind == 'punch':                                   # employee punched on the machine: show the slip (it prints by itself)
            uid, text, state, err = info
            entered.set(uid); fresh[0] = True
            if state == 'notfound': cur_slip[0] = None; pstat.set(''); show(f'\n\n\nID {uid}\nwas not found in the reports', True)
            else:
                if state == 'show': cur_slip[0] = text; show(text); pstat_lbl.config(fg='#555'); pstat.set('Printing...')
                elif state == 'ok': pstat_lbl.config(fg=INK); pstat.set('Printed')
                else: pstat_lbl.config(fg=RED); pstat.set('Print failed')
        else:
            sb.STATS['printer'] = f'Error: {info}'; pstat_lbl.config(fg=RED); pstat.set('Print failed')
            messagebox.showerror('Printer', f'Could not print:\n{info}')
    while not q.empty():
        log.insert('end', q.get()); log.see('end')
    while not tray_q.empty():
        action = tray_q.get()
        if action == 'open': root.deiconify(); root.lift(); root.focus_force()
        elif action == 'exit': request_exit()
    run, S, dts = bool(th and th.is_alive() and not sb.STOP.is_set()), sb.STATS, sb.report_dates()
    pill.config(text='\u25cf  RUNNING' if run else '\u25cf  STOPPED', bg=PRIMARY if run else '#eeeeee', fg='white' if run else '#111111')
    sv['mach'].set(f'{cfg["device_ip"]}:{cfg["device_port"]}'); sv['mach_state'].set('Connected' if S['connected'] else 'Not connected')
    cardlbl['mach_state'].config(fg=INK if S['connected'] else PRIMARY, font=('Segoe UI', 10, 'bold'))
    sv['prn'].set((f'Network {cfg["printer_ip"]}' if cfg['mode'] == 'network' else f'USB / Windows\n{cfg["printer_name"] or "(none selected)"}') + f'\nLast print: {S["printer"]}')
    f = lambda k: f'{k} report: ' + (f'{dts[k]:%d %b %Y}' if k in dts else 'not loaded')
    sv['sync'].set(f'Auto-update: {sb.SYNC["result"]}\nLast check: {sb.SYNC["last"]}')
    sv['watch'].set(f'Auto-load: put WH / LB files in the reports folder - checked every {WATCH_SEC} s\nLast load: {WATCH["last"]}')
    sv['wh'].set(f('WH')); sv['lb'].set(f('LB')); sv['emp'].set('Loading reports...' if S['loading'] else f'{len(sb.DATA)} employees loaded' + (f'\nError: {S["error"]}' if S['error'] else ''))
    sv['slips'].set(f'Slips printed: {S["slips"]}'); sv['last'].set(f'Last punch:\n{S["last"]}')
    root.after(500, poll)


def tick():                                # hourly (or as set) copy of new reports from the linked folder
    sb.SOURCE_DIR = cfg['source_dir']
    if sb.SOURCE_DIR: threading.Thread(target=sb.sync_reports, daemon=True).start()
    root.after((int(cfg['sync_min']) if str(cfg['sync_min']).isdigit() and int(cfg['sync_min']) > 0 else 60) * 60000, tick)


threading.Thread(target=sb.refresh, daemon=True).start()
threading.Thread(target=watcher, daemon=True).start()          # auto-detects WH / LB files dropped into the reports folder
root.after(3000, tick)
start_tray()
poll()
if cfg['autorun']: root.after(1500, start)
root.mainloop()
