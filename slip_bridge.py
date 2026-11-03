"""Punch ID -> attendance + leave balance slip on a network thermal printer.
Works with ZKTeco network devices (LP400, UFace 900, ...) that allow live punch capture.

Setup : pip install pyzk pandas openpyxl
Folder: keep this file next to the two reports (.xlsx, or the HTML-table .xls export) NAMED exactly:
          WH (DD MMM, YYYY).xls / .xlsx   e.g. WH (29 Oct, 2026).xls   (attendance)
          LB (DD MMM, YYYY).xls / .xlsx   e.g. LB (29 Oct, 2026).xls   (leave balance)
Daily : drop the new WH report and Leave report (.xlsx) into this folder - no restart needed.
        The newest file of each kind is picked up automatically on the next punch.
        If a new file is unreadable (half-copied, wrong format) the old data stays in use.
Test  : python slip_bridge.py --test 401708     (prints slip on screen, no hardware needed)
Live  : python slip_bridge.py                   (listens to the device and prints slips)
"""
import glob, html, json, os, re, shutil, socket, sys, threading, time
from datetime import datetime
import pandas as pd

DEVICE_IP, DEVICE_PORT, COMM_KEY = '192.168.1.201', 4370, 0
PRINTER_IP, PRINTER_PORT = '192.168.1.250', 9100   # network thermal printer (raw ESC/POS)
COLS, DAYS = 40, 30                                 # 80 mm paper: 40 | 58 mm paper: 32
DUPLICATE_SECONDS = 600                             # same person ignored for 10 minutes
SOURCE_DIR, SYNC_MIN = '', 60                       # linked folder the daily reports are copied from, and how often (minutes)
PRINT_MODE = 'raw'                                  # 'raw' = ESC/POS thermal printer | 'text' = normal text via the Windows driver (any printer)
PRINTER_NAME = ''                                  # USB / Windows printer name; empty = use the network IP above
ID_MAP = {}                                         # only if device IDs differ: {'1': '401708'}


def flags(rem):   # L = Late, E = Early going, H = Half day
    r = str(rem).lower()
    return ' '.join(c for c, k in (('L', 'late'), ('E', 'early'), ('H', 'half')) if k in r)


LEAVE_RULES = [   # order matters: specific first, general last. Only these 17 leave types (+ 'Off Day') are shown on the slip.
    (r'half\s*day\s*casual|halfday.*casual', 'Half Day Casual'),
    (r'short\s*casual', 'Short Casual Leave'),
    (r'casual', 'Casual Leave'),
    (r'half\s*day\s*sick|halfday.*sick', 'Half Day Sick'),
    (r'short\s*sick', 'Short Sick Leave'),
    (r'sick', 'Sick Leave'),
    (r'annual', 'Annual Leave'),
    (r'compensatory', 'Compensatory Leave'),
    (r'leave\s*without\s*pay', 'Leave Without Pay'),
    (r'social\s*security', 'Social Security Leave'),
    (r'off?ic(i)?al\s*visit', 'Official Visit'),
    (r'paternity', 'Paternity Leave'),
    (r'maternity', 'Maternity Leave'),
    (r'hajj|pilgrimage', 'Hajj / Pilgrimage'),
    (r'suspended', 'Suspended'),
    (r'iddat', 'Iddat Leave'),
    (r'lay\s*off', 'Lay Off Leave'),
]
OFF_DAY = r'\boff[\s_-]*day'      # 'Off Day', 'Off Day Invalid' ... -> only 'Off Day'


def clean_remark(text):
    """WH remark -> 'Off Day', one of the 17 leave types, 'Off Day-(Leave type)' when both are present, or '' if none.
    e.g. 'Off Day Invalid' -> 'Off Day' | '(Half Day Casual)-On Time' -> 'Half Day Casual' | 'Off Day-(Casual Leave)'."""
    s = str(text or '').lower()
    leave = next((name for pat, name in LEAVE_RULES if re.search(pat, s)), '')
    if re.search(OFF_DAY, s):
        return f'Off Day-({leave})' if leave else 'Off Day'
    return leave


def shift_code(v):
    """Roster code as short text: NaN -> '', 3.0 -> '3'."""
    if v is None or (not isinstance(v, str) and pd.isna(v)):
        return ''
    if isinstance(v, float) and v == int(v):
        v = int(v)
    return str(v).strip()


SLIP_HOOK = None   # set by the window app: SLIP_HOOK(uid, text, state, error) with state 'show' | 'ok' | 'err' | 'notfound'
STOP = threading.Event()   # set by the window app to stop live()
STATS = {'error': '', 'loading': False, 'connected': False, 'slips': 0, 'last': '-', 'printer': '-'}   # shown on the app overview


def fdate(p):
    m = re.search(r'\((\d{2} [A-Za-z]{3}, \d{4})\)', os.path.basename(p))
    try:
        return datetime.strptime(m.group(1).title(), '%d %b, %Y')
    except Exception:
        return datetime.min


def newest(pat):   # newest by the date in the file name, then by modified time
    files = [f for f in glob.glob(pat) if not f.endswith('.tmp')]
    if not files:
        raise FileNotFoundError(f'No report named {pat} (both WH and LB reports are needed)')
    return max(files, key=lambda p: (fdate(p), os.path.getmtime(p)))


def report_dates():
    out = {}
    for k, pat in (('WH', 'WH (*).xls*'), ('LB', 'LB (*).xls*')):
        try:
            out[k] = fdate(newest(pat))
        except Exception:
            pass
    return out


def sig():
    return [(p, os.path.getmtime(p)) for p in (newest('WH (*).xls*'), newest('LB (*).xls*'))]


_ROW = re.compile(r'<tr[^>]*>(.*?)</tr>', re.S | re.I)
_CELL = re.compile(r'<t[dh][^>]*>(.*?)</t[dh]>', re.S | re.I)
_TAG = re.compile(r'<[^>]+>')
WH_COLS = ['Attendance Date', 'Emp Id', 'Employee Name', 'Roster Code', 'Emp In', 'Emp Out', 'Remarks']   # Roster Code is optional in the file


def html_rows(path, limit_chars=None):
    """Stream the rows of an HTML-table '.xls' export (e.g. Decibel reports) as lists of cell text."""
    buf, read = '', 0
    with open(path, encoding='utf-8', errors='replace') as f:
        while True:
            chunk = f.read(4 << 20)
            if not chunk:
                break
            if not read and re.search(r'<frameset|Excel Workbook Frameset', chunk[:20000], re.I):
                raise ValueError('web-page style .xls (needs its _files folder): open it in Excel and save as .xlsx')
            read, buf = read + len(chunk), buf + chunk
            cut = buf.lower().rfind('</tr>')
            if cut < 0:
                continue
            part, buf = buf[:cut + 5], buf[cut + 5:]
            for m in _ROW.finditer(part):
                yield [html.unescape(_TAG.sub('', c)).replace('\xa0', ' ').strip() for c in _CELL.findall(m.group(1))]
            if limit_chars and read >= limit_chars:
                return


def read_report(path, kind, quick=False):
    """Report as a DataFrame. Accepts .xlsx and HTML-table .xls. WH: named columns; LB: positional (18 columns)."""
    head = open(path, 'rb').read(8)
    if head[:2] == b'PK':
        return pd.read_excel(path, engine='openpyxl', nrows=5 if quick else None, **({} if kind == 'WH' else {'header': None, 'skiprows': 2}))
    if head[:4] == b'\xd0\xcf\x11\xe0':
        raise ValueError('old binary .xls is not supported: open it in Excel and save as .xlsx')
    rows, idx = html_rows(path, 300000 if quick else None), None
    if kind == 'WH':
        data = []
        for r in rows:
            if idx is None:
                if 'Emp Id' in r and 'Attendance Date' in r:
                    low = [x.strip().lower() for x in r]
                    idx, n = [(next((i for i, x in enumerate(low) if 'roster' in x), -1) if c == 'Roster Code'
                               else (low.index(c.lower()) if c.lower() in low else -1)) for c in WH_COLS], len(r)
                continue
            if len(r) == n:
                data.append([r[i] if i >= 0 else '' for i in idx])
        if idx is None:
            raise ValueError('WH report header row (Attendance Date, Emp Id ...) not found')
        return pd.DataFrame(data, columns=WH_COLS)
    return pd.DataFrame([r for r in rows if len(r) == 18 and r[0].isdigit()])


def eid(v):
    """Employee ID as plain text, letters removed: 219033.0 -> '219033', '219033x' -> '219033', '906137 (906137)' -> '906137'."""
    if isinstance(v, float) and v == int(v):
        v = int(v)
    return re.sub(r'^[A-Za-z]+|[A-Za-z]+$', '', re.sub(r'\s*\(.*\)$', '', str(v).strip()))


def hm(v):
    """Any time value (time, datetime, text like '8:45' or '08:45:10', Excel fraction) -> 'HH:MM' or ''."""
    if v is None or pd.isna(v) or v == '':
        return ''
    if hasattr(v, 'strftime'):
        return v.strftime('%H:%M')
    if isinstance(v, (int, float)) and 0 <= v < 1:
        m = round(v * 1440)
        return f'{m // 60 % 24:02d}:{m % 60:02d}'
    m = re.match(r'^(\d{1,2}):(\d{2})', str(v).strip())
    return f'{int(m.group(1)):02d}:{m.group(2)}' if m else str(v).strip()[:5]


def load():
    wh = read_report(newest('WH (*).xls*'), 'WH')
    lv = read_report(newest('LB (*).xls*'), 'LB')
    nm = lambda x: str(x) if pd.notna(x) else ''
    d, lv = {}, lv[lv[3].notna() & (lv[3].astype(str).str.strip() != '')]
    c = [pd.to_numeric(lv[i], errors='coerce').fillna(0).round(2).tolist() for i in (6, 7, 9, 10, 11, 13, 14, 15, 17)]
    dups = []
    for k, (uid, n) in enumerate(zip(lv[3].map(eid), lv[2])):
        if uid in d:
            dups.append(uid)
        d[uid] = {'n': nm(n), 'att': [], 'lv': {'Casual': [c[0][k], c[1][k], c[2][k]],
                  'Sick': [c[3][k], c[4][k], c[5][k]], 'Annual': [c[6][k], c[7][k], c[8][k]]}}
    wh = wh.dropna(subset=['Emp Id'])
    wh = wh[wh['Emp Id'].astype(str).str.strip() != '']
    wh = wh.assign(_d=pd.to_datetime(wh['Attendance Date'].astype(str).str.strip(), errors='coerce')).dropna(subset=['_d']).sort_values('_d', kind='stable')
    rem = wh['Remarks'].fillna('').astype(str).tolist()
    rc = next((c for c in wh.columns if 'roster' in str(c).lower()), None)      # Roster Code column (any header containing 'roster')
    shifts = wh[rc].map(shift_code).tolist() if rc is not None else [''] * len(wh)
    for uid, n, dt, i, o, r, sh in zip(wh['Emp Id'].map(eid), wh['Employee Name'], wh['_d'].dt.strftime('%d-%b'),
                                       wh['Emp In'].map(hm), wh['Emp Out'].map(hm), rem, shifts):
        d.setdefault(uid, {'n': nm(n), 'att': [], 'lv': {}})['att'].append([dt, i, o, r, flags(r), sh, clean_remark(r)])
    if dups:
        print(f'Warning: {len(dups)} duplicate employee IDs after removing letters, e.g. {dups[:3]} (the last one is used)')
    return d


DATA, today, SIG = {}, {}, None   # today = {id: [first punch, last punch]} (resets if program restarts)


CACHE, BAD, _lock = 'cache.json', None, threading.Lock()


def refresh():
    """Reload reports when newer files appear. Parsed data is cached (restarts are instant);
    old data is kept if a new file fails, and a failed file is not retried on every punch."""
    global DATA, SIG, BAD
    if not _lock.acquire(blocking=False):
        return
    s = None
    try:
        s = sig()
        if s == SIG or s == BAD:
            return
        STATS['loading'] = True
        key = [[p, m] for p, m in s] + [['v', 6]]      # bump v when the parsing rules change
        try:
            c = json.load(open(CACHE, encoding='utf-8'))
            d = c['data'] if c['sig'] == key else None
        except Exception:
            d = None
        if d is None:
            d = load()
            json.dump({'sig': key, 'data': d}, open(CACHE, 'w', encoding='utf-8'))
        DATA, SIG = d, s
        STATS['error'] = ''
        print('Reports loaded:', [os.path.basename(p) for p, _ in s], f'({len(d)} employees)')
    except Exception as ex:
        if s:
            BAD = s
        STATS['error'] = str(ex)[:90]
        print('Report reload failed (old data kept):', ex)
    finally:
        STATS['loading'] = False
        _lock.release()


NAME = {k: re.compile(rf'^{k} \((\d{{2}} [A-Za-z]{{3}}, \d{{4}})\)\.xlsx?$', re.I) for k in ('WH', 'LB')}
SYNC, _sync_lock = {'last': '-', 'result': 'Linked folder not set'}, threading.Lock()


def check_file(path, kind):
    """Quick sanity check of the first rows; raises ValueError with a readable message."""
    try:
        df = read_report(path, kind, quick=True)
    except ValueError:
        raise
    except Exception as ex:
        raise ValueError(f'cannot read file ({ex})')
    if kind == 'WH' and not {'Emp Id', 'Attendance Date', 'Emp In', 'Emp Out', 'Employee Name', 'Remarks'} <= set(df.columns):
        raise ValueError('missing columns in WH report')
    if kind == 'LB' and (df.shape[1] < 18 or df.empty):
        raise ValueError('unexpected leave balance layout (18 columns expected)')


def sync_reports():
    """Copy the newest WH / LB report from SOURCE_DIR into this folder when it is new or changed, then reload."""
    if not _sync_lock.acquire(blocking=False):
        return
    msg, changed = [], False
    try:
        SYNC['last'] = datetime.now().strftime('%d %b %H:%M')
        if not SOURCE_DIR or not os.path.isdir(SOURCE_DIR):
            SYNC['result'] = 'Linked folder not found'
            print('Auto-update:', SYNC['result'], SOURCE_DIR)
            return
        for kind in ('WH', 'LB'):
            tmp = None
            try:
                names = [f for f in os.listdir(SOURCE_DIR) if NAME[kind].match(f)]
                if not names:
                    msg.append(f'{kind}: no file'); continue
                f = max(names, key=lambda n: (fdate(n), os.path.getmtime(os.path.join(SOURCE_DIR, n))))
                src, d = os.path.join(SOURCE_DIR, f), fdate(f)
                dst, cur = f'{kind} ({d:%d %b}, {d:%Y}){os.path.splitext(f)[1].lower()}', report_dates().get(kind)
                if d == datetime.min:
                    msg.append(f'{kind}: bad date in file name'); continue
                if cur and d < cur:
                    msg.append(f'{kind}: {f} is older than the loaded one'); continue
                if time.time() - os.path.getmtime(src) < 60:
                    msg.append(f'{kind}: file is still being written, retry later'); continue
                if os.path.exists(dst) and os.path.getsize(dst) == os.path.getsize(src) and int(os.path.getmtime(dst)) == int(os.path.getmtime(src)):
                    msg.append(f'{kind} {d:%d %b} up to date'); continue
                tmp = dst + '.tmp'
                shutil.copy2(src, tmp); check_file(tmp, kind); os.replace(tmp, dst)
                msg.append(f'{kind} {d:%d %b} updated'); changed = True
            except Exception as ex:
                msg.append(f'{kind}: {str(ex)[:60]}')
                if tmp and os.path.exists(tmp):
                    os.remove(tmp)
        SYNC['result'] = '; '.join(msg)
        print('Auto-update:', SYNC['result'])
    finally:
        _sync_lock.release()
    if changed:
        for k in ('WH', 'LB'):          # keep only the 3 newest local copies of each report
            for p in sorted((x for x in glob.glob(f'{k} (*).xls*') if not x.endswith('.tmp')), key=lambda p: (fdate(p), os.path.getmtime(p)), reverse=True)[3:]:
                try: os.remove(p)
                except OSError: pass
        refresh()


def sync_loop():
    while True:
        sync_reports()
        time.sleep(max(1, SYNC_MIN) * 60)


def slip(uid, ts):
    uid = eid(uid)
    e, L = DATA.get(uid), '-' * COLS
    if not e:
        return None
    rows = e['att'][-DAYS:]
    shw = min(8, max([5] + [len(a[5]) for a in rows if len(a) > 5]) + 1)      # Shift column width (fits the longest roster code)
    space = COLS - (7 + shw + 12)                                              # room left for Remarks on the same line
    o = ['ATTENDANCE SLIP'.center(COLS), L, f'Name : {e["n"]}', f'ID   : {uid}',
         f'Punch: {ts:%d-%b-%Y %H:%M}', L, f'{"Date":<7}{"Shift":<{shw}}{"In":<6}{"Out":<6}Remarks']
    for a in rows:
        sh = (a[5] if len(a) > 5 else '') or '--'
        rem = (a[6] if len(a) > 6 else clean_remark(a[3])) or (a[4] if a[1] or a[2] else '')   # leave type, else L/E/H flags
        line = f'{a[0]:<7}{sh[:shw - 1]:<{shw}}{a[1] or "--":<6}{a[2] or "--":<6}'
        if len(rem) <= space:
            o.append((line + rem).rstrip())
        else:                                   # long leave name: continue on the next line
            o += [line.rstrip(), '  ' + rem[:COLS - 2]]
    if uid in today:
        f, l = today[uid]
        o.append(f'{"Today":<7}{"":<{shw}}{f:<6}{(l if l != f else "--"):<6}')
    if rows:
        o += [L, f'Late: {sum("L" in a[4].split() for a in rows)}   Early going: {sum("E" in a[4].split() for a in rows)}', 'L=Late  E=Early going']
    o += [L, 'LEAVE BALANCE', f'{"":<9}{"Allowed":>8}{"Used":>8}{"Left":>8}']
    o += [f'{k:<9}{v[0]:>8g}{v[1]:>8g}{v[2]:>8g}' for k, v in e['lv'].items()] or ['No leave data found']
    return '\n'.join(o + [L, 'Thank you'.center(COLS)])


def printer_problem(h):
    """(problem text, jobs waiting) for an open Windows printer handle; empty text = no problem found."""
    import win32print
    info = win32print.GetPrinter(h, 2)
    flags = ((1, 'paused'), (2, 'in error'), (8, 'jammed'), (0x10, 'out of paper'), (0x40, 'having a paper problem'),
             (0x80, 'offline'), (0x400000, 'cover open'))
    bad = [n for b, n in flags if info['Status'] & b]
    if info['Attributes'] & 0x400:
        bad.append('set to "Use Printer Offline"')
    return ', '.join(bad), info['cJobs']


def gdi_print(text):
    """Print as normal text through the Windows printer driver (works on any installed printer)."""
    import win32con, win32ui
    dc = win32ui.CreateDC()
    dc.CreatePrinterDC(PRINTER_NAME)
    try:
        width, height, dpi = dc.GetDeviceCaps(win32con.HORZRES), dc.GetDeviceCaps(win32con.VERTRES), dc.GetDeviceCaps(win32con.LOGPIXELSY)
        em = int(min(width / (COLS * 0.6), dpi * 9 / 72))        # 9 pt, or smaller so COLS characters fit the paper width
        dc.SelectObject(win32ui.CreateFont({'name': 'Courier New', 'height': -em}))
        step, y = int(em * 1.25), 0
        dc.StartDoc('Attendance slip')
        dc.StartPage()
        for line in text.split('\n'):
            if y + step > height:
                dc.EndPage(); dc.StartPage(); y = 0
            dc.TextOut(0, y, line.rstrip()); y += step
        dc.EndPage()
        dc.EndDoc()
    finally:
        dc.DeleteDC()


def print_slip(text):
    data = b'\x1b@' + text.encode('ascii', 'replace') + b'\n\n\n\n\x1d\x56\x00'   # init, text, feed, cut
    if PRINTER_NAME:                                    # printer installed in Windows (USB, shared, office ...)
        import win32print
        h = win32print.OpenPrinter(PRINTER_NAME)
        try:
            bad, jobs = printer_problem(h)
            if bad:
                raise RuntimeError(f'Printer "{PRINTER_NAME}" is {bad}. Fix it in Windows (Settings > Printers & scanners)')
            if PRINT_MODE == 'text':
                gdi_print(text)
            else:
                win32print.StartDocPrinter(h, 1, ('Slip', None, 'RAW'))
                win32print.StartPagePrinter(h)
                win32print.WritePrinter(h, data)
                win32print.EndPagePrinter(h)
                win32print.EndDocPrinter(h)
            print(f'  Windows print queue: {win32print.GetPrinter(h, 2)["cJobs"]} job(s) waiting')
        finally:
            win32print.ClosePrinter(h)
        return
    with socket.create_connection((PRINTER_IP, PRINTER_PORT), timeout=10) as s:
        s.sendall(data)


def _hook(uid, text, state, err):
    try:
        if SLIP_HOOK: SLIP_HOOK(uid, text, state, err)
    except Exception:
        pass


def live():
    from zk import ZK
    last = {}
    while not STOP.is_set():
        try:
            conn = ZK(DEVICE_IP, port=DEVICE_PORT, timeout=10, password=COMM_KEY).connect()
            STATS['connected'] = True
            print('Device connected - waiting for punches...')
            for att in conn.live_capture():
                if STOP.is_set():
                    break
                if att is None:
                    continue
                uid = eid(ID_MAP.get(str(att.user_id), str(att.user_id)))
                if time.time() - last.get(uid, 0) < DUPLICATE_SECONDS:
                    continue
                last[uid] = t0 = time.time()
                refresh()
                hm = att.timestamp.strftime('%H:%M')
                today[uid] = [today.get(uid, [hm])[0], hm]
                text = slip(uid, att.timestamp)
                print(f'{att.timestamp} ID {uid}:', 'printing' if text else 'ID not found in reports')
                _hook(uid, text, 'show' if text else 'notfound', '')
                if text:
                    try:
                        print_slip(text)
                        _hook(uid, text, 'ok', '')
                        STATS.update(slips=STATS['slips'] + 1, printer='OK',
                                     last=f'{att.timestamp:%H:%M:%S}  ID {uid}  {DATA[uid]["n"]}')
                        print(f'  slip sent to printer in {time.time() - t0:.2f} s')
                    except Exception as ex:
                        STATS['printer'] = f'Error: {ex}'
                        print('  Printer error:', ex)
                        _hook(uid, text, 'err', str(ex))
            try:
                conn.end_live_capture(); conn.disconnect()
            except Exception:
                pass
        except Exception as ex:
            STATS['connected'] = False
            print('Connection problem, retrying in 10 s:', ex)
            time.sleep(10)


if __name__ == '__main__':
    refresh()
    if len(sys.argv) > 2 and sys.argv[1] == '--test':
        print(slip(sys.argv[2], datetime.now()) or 'ID not found in the reports')
    else:
        if SOURCE_DIR:
            threading.Thread(target=sync_loop, daemon=True).start()
        live()
