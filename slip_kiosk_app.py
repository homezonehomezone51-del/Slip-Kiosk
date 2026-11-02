"""Slip Kiosk - prints an attendance + leave slip for every punch. Needs slip_bridge.py next to it."""
import json, os, queue, re, shutil, sys, threading
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, scrolledtext, simpledialog, ttk
import pandas as pd

LOGO_B64 = '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'
BASE = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
DATA, CFG = os.path.join(BASE, 'reports'), os.path.join(BASE, 'config.json')
os.makedirs(DATA, exist_ok=True)
os.chdir(DATA)
q = queue.Queue()


class W:                                   # send all print() output to the log window
    def write(self, s): q.put(s)
    def flush(self): pass


sys.stdout = W()
import slip_bridge as sb                   # engine: reads the newest reports in the current folder

cfg = {'device_ip': '192.168.1.201', 'device_port': '4370', 'comm_key': '0', 'printer_ip': '192.168.1.250',
       'paper': '80', 'days': '30', 'mode': 'network', 'printer_name': '', 'source_dir': '', 'sync_min': '60', 'plain': False, 'autorun': False}
if os.path.exists(CFG):
    cfg.update(json.load(open(CFG)))
BAT = os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup', 'SlipKiosk.bat')
RED, NAVY, BG, FN = '#c8201e', '#0b1f33', '#f4f6f8', ('Segoe UI', 9)
NAME = {k: re.compile(rf'^{k} \((\d{{2}} [A-Za-z]{{3}}, \d{{4}})\)\.xlsx?$', re.I) for k in ('WH', 'LB')}

root = tk.Tk(); root.title('Slip Kiosk - Servis Tyres'); root.configure(bg=BG)
v = {k: tk.StringVar(value=str(cfg[k])) for k in ('device_ip', 'device_port', 'comm_key', 'printer_ip', 'paper', 'days', 'printer_name', 'mode', 'source_dir', 'sync_min')}
auto, plain = tk.BooleanVar(value=cfg['autorun']), tk.BooleanVar(value=cfg['plain'])

# ---- header with logo and status pill
hd = tk.Frame(root, bg='white'); hd.pack(fill='x')
try:
    logo = tk.PhotoImage(data=LOGO_B64)
    tk.Label(hd, image=logo, bg='white').pack(side='left', padx=12, pady=6)
except Exception:
    pass
tk.Label(hd, text='Attendance Slip Kiosk', font=('Segoe UI', 18, 'bold'), fg=NAVY, bg='white').pack(side='left')
pill = tk.Label(hd, text='STOPPED', font=('Segoe UI', 11, 'bold'), fg='white', bg='#888', padx=14, pady=4); pill.pack(side='right', padx=16)
tk.Frame(root, bg=RED, height=4).pack(fill='x')

# ---- overview cards
cards = tk.Frame(root, bg=BG); cards.pack(fill='x', padx=10, pady=8)
sv = {k: tk.StringVar(value='-') for k in ('mach', 'prn', 'wh', 'lb', 'emp', 'sync', 'slips', 'last')}
for col, (title, keys) in enumerate([('MACHINE', ['mach']), ('PRINTER', ['prn']), ('REPORTS', ['wh', 'lb', 'emp', 'sync']), ('ACTIVITY', ['slips', 'last'])]):
    f = tk.LabelFrame(cards, text=title, bg='white', fg=NAVY, font=('Segoe UI', 8, 'bold'), padx=8, pady=4)
    f.grid(row=0, column=col, sticky='nsew', padx=4); cards.columnconfigure(col, weight=1, uniform='c')
    for k in keys: tk.Label(f, textvariable=sv[k], bg='white', font=FN, anchor='w', justify='left', wraplength=170).pack(fill='x')


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
    f = tk.LabelFrame(parent, text=title, bg='white', fg=NAVY, font=('Segoe UI', 9, 'bold'), padx=8, pady=4)
    f.grid(row=0, column=col, sticky='nsew', padx=4); parent.columnconfigure(col, weight=1, uniform='s'); return f


st = tk.Frame(root, bg=BG); st.pack(fill='x', padx=10)
mf, pf = box(st, 'Machine and slip', 0), box(st, 'Printer connection (tick the one to use)', 1)
for i, (t, k) in enumerate([('Machine IP', 'device_ip'), ('Machine port', 'device_port'), ('Comm Key', 'comm_key'),
                            ('Paper width (58/80 mm)', 'paper'), ('Days shown on slip', 'days')]):
    tk.Label(mf, text=t, bg='white', font=FN).grid(row=i, column=0, sticky='e', padx=4, pady=2)
    tk.Entry(mf, textvariable=v[k], width=18).grid(row=i, column=1, sticky='w')
tk.Radiobutton(pf, text='Network printer (IP)', variable=v['mode'], value='network', bg='white', font=FN).grid(row=0, column=0, sticky='w')
tk.Entry(pf, textvariable=v['printer_ip'], width=22).grid(row=0, column=1, sticky='w', padx=6)
tk.Radiobutton(pf, text='USB / Windows printer', variable=v['mode'], value='usb', bg='white', font=FN).grid(row=1, column=0, sticky='w', pady=6)
cb = ttk.Combobox(pf, textvariable=v['printer_name'], values=printers(), width=30, state='readonly'); cb.grid(row=1, column=1, sticky='w', padx=6)
ttk.Button(pf, text='Refresh', width=8, command=lambda: cb.config(values=printers())).grid(row=1, column=2)
def open_queue():
    n = v['printer_name'].get().strip()
    if not n: messagebox.showinfo('Print queue', 'Select a USB / Windows printer first'); return
    import subprocess
    subprocess.Popen(['rundll32', 'printui.dll,PrintUIEntry', '/o', '/n', n])


tk.Checkbutton(pf, text='Office / laser / inkjet printer (print as normal text)', variable=plain, bg='white', font=FN).grid(row=2, column=0, columnspan=2, sticky='w')
ttk.Button(pf, text='Print queue', width=10, command=open_queue).grid(row=2, column=2)
tk.Checkbutton(pf, text='Start automatically with Windows', variable=auto, bg='white', font=FN).grid(row=3, column=0, columnspan=2, sticky='w')


af = tk.LabelFrame(root, text='Reports auto-update (linked folder holding WH (DD MMM, YYYY).xls/.xlsx and LB (DD MMM, YYYY).xls/.xlsx)', bg='white', fg=NAVY, font=('Segoe UI', 9, 'bold'), padx=8, pady=4)
af.pack(fill='x', padx=14, pady=(8, 0))
tk.Label(af, text='Linked folder', bg='white', font=FN).pack(side='left')
tk.Entry(af, textvariable=v['source_dir'], width=48).pack(side='left', padx=4)
ttk.Button(af, text='Browse', command=lambda: v['source_dir'].set(filedialog.askdirectory() or v['source_dir'].get())).pack(side='left')
tk.Label(af, text='  Check every (min)', bg='white', font=FN).pack(side='left')
tk.Entry(af, textvariable=v['sync_min'], width=5).pack(side='left', padx=4)
ttk.Button(af, text='Check now', command=lambda: safe_apply() and threading.Thread(target=sb.sync_reports, daemon=True).start()).pack(side='left', padx=6)


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


def load_report(kind):                     # kind: 'WH' (attendance) or 'LB' (leave balance)
    f = filedialog.askopenfilename(title=f'Select {kind} report (.xls or .xlsx)', filetypes=[('Report files', '*.xls *.xlsx')])
    if not f: return
    m = NAME[kind].match(os.path.basename(f))
    try: d = datetime.strptime(m.group(1).title(), '%d %b, %Y') if m else None
    except ValueError: d = None
    if not d:
        messagebox.showerror('Wrong file name', f'The file name must be:  {kind} (DD MMM, YYYY).xls  or  .xlsx\nExample:  {kind} (29 Oct, 2026).xls\n\nSelected: {os.path.basename(f)}'); return
    cur = sb.report_dates().get(kind)
    if cur and d < cur:
        messagebox.showerror('Older report', f'The loaded {kind} report is dated {cur:%d %b %Y}.\nThis file ({d:%d %b %Y}) is older and will not be used.'); return
    dst = os.path.join(DATA, f'{kind} ({d:%d %b}, {d:%Y}){os.path.splitext(f)[1].lower()}')
    shutil.copyfile(f, dst + '.tmp')
    try: sb.check_file(dst + '.tmp', kind)
    except Exception as e:
        os.remove(dst + '.tmp'); messagebox.showerror('Could not read file', f'Please check the file.\n{e}'); return
    os.replace(dst + '.tmp', dst)
    threading.Thread(target=sb.refresh, daemon=True).start()


def test(do_print):
    if not safe_apply(): return
    if sb.STATS['loading']: messagebox.showinfo('Slip', 'Reports are still loading, try again in a moment'); return
    uid = simpledialog.askstring('Slip', 'Enter Employee ID')
    if not uid: return
    text = sb.slip(uid.strip(), datetime.now())
    if not text: messagebox.showinfo('Slip', 'This ID was not found in the reports'); return
    print(text)
    if do_print:
        try: sb.print_slip(text); sb.STATS['printer'] = 'OK (test print)'
        except Exception as e: sb.STATS['printer'] = f'Error: {e}'; messagebox.showerror('Printer', f'Could not print:\n{e}')


bar = tk.Frame(root, bg=BG); bar.pack(pady=8)
for t, c in [('Save + Start', start), ('Stop', stop), ('Load WH report', lambda: load_report('WH')),
             ('Load LB report', lambda: load_report('LB')), ('Preview slip', lambda: test(False)), ('Test print', lambda: test(True))]:
    ttk.Button(bar, text=t, command=c).pack(side='left', padx=3)
log = scrolledtext.ScrolledText(root, width=96, height=12, font=('Courier New', 9)); log.pack(padx=10, pady=(0, 10), fill='both', expand=True)


def poll():
    while not q.empty():
        log.insert('end', q.get()); log.see('end')
    run, S, dts = bool(th and th.is_alive() and not sb.STOP.is_set()), sb.STATS, sb.report_dates()
    pill.config(text='RUNNING' if run else 'STOPPED', bg='#1e9e57' if run else '#888')
    sv['mach'].set(f'{cfg["device_ip"]}:{cfg["device_port"]}\n' + ('Connected' if S['connected'] else 'Not connected'))
    sv['prn'].set((f'Network {cfg["printer_ip"]}' if cfg['mode'] == 'network' else f'USB / Windows\n{cfg["printer_name"] or "(none selected)"}') + f'\nLast print: {S["printer"]}')
    f = lambda k: f'{k} report: ' + (f'{dts[k]:%d %b %Y}' if k in dts else 'not loaded')
    sv['sync'].set(f'Auto-update: {sb.SYNC["result"]}\nLast check: {sb.SYNC["last"]}')
    sv['wh'].set(f('WH')); sv['lb'].set(f('LB')); sv['emp'].set('Loading reports...' if S['loading'] else f'{len(sb.DATA)} employees loaded' + (f'\nError: {S["error"]}' if S['error'] else ''))
    sv['slips'].set(f'Slips printed: {S["slips"]}'); sv['last'].set(f'Last punch:\n{S["last"]}')
    root.after(500, poll)


def tick():                                # hourly (or as set) copy of new reports from the linked folder
    sb.SOURCE_DIR = cfg['source_dir']
    if sb.SOURCE_DIR: threading.Thread(target=sb.sync_reports, daemon=True).start()
    root.after((int(cfg['sync_min']) if str(cfg['sync_min']).isdigit() and int(cfg['sync_min']) > 0 else 60) * 60000, tick)


threading.Thread(target=sb.refresh, daemon=True).start()
root.after(3000, tick)
poll()
if cfg['autorun']: root.after(1500, start)
root.mainloop()
