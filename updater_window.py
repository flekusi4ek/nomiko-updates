"""Independent NOMIKO updater UI: a small, private Tk window, no Qt DLL locks.

Indeterminate motion is intentional while NSIS extracts files: the installer
does not report byte-level progress. We show real *stages*, never fake percent.
Only the worker thread touches disk/processes; Tk widgets stay on the UI thread.
"""
from __future__ import annotations

import os
from pathlib import Path
from queue import Empty, SimpleQueue
import subprocess
import threading
import time
import tkinter as tk

BG = '#0F1119'
PANEL = '#1A1D29'
BORDER = '#333647'
ACCENT = '#A18AFF'
TEXT = '#F1F2F8'
MUTED = '#9A9EB2'
SUCCESS = '#79DFB0'
ERROR = '#FF8C98'
STEPS = ('Close browser', 'Verify update', 'Install NOMIKO', 'Finish')


def _rounded(canvas, x1, y1, x2, y2, radius, **kwargs):
    """Draw a rounded panel as one anti-aliased-ish Tk spline polygon."""
    r = min(radius, (x2 - x1) / 2, (y2 - y1) / 2)
    points = [
        x1+r, y1, x2-r, y1, x2, y1, x2, y1+r,
        x2, y2-r, x2, y2, x2-r, y2,
        x1+r, y2, x1, y2, x1, y2-r,
        x1, y1+r, x1, y1, x1+r, y1,
    ]
    return canvas.create_polygon(points, smooth=True, splinesteps=16, **kwargs)


class UpdateWindow:
    def __init__(self, worker, *, app_dir, installer, master=None):
        self.worker = worker
        self.app_dir = Path(app_dir)
        self.installer = Path(installer)
        self.version = self.installer.name.removeprefix('NOMIKO-Setup-').removesuffix('.exe')
        self.events = SimpleQueue()
        self.completed = False
        self.result = 10
        self.phase = 0
        self.animation = 0
        self.root = master or tk.Tk()
        self.root.title('NOMIKO · Update')
        self.root.geometry('620x438')
        self.root.minsize(620, 438)
        self.root.maxsize(620, 438)
        self.root.configure(bg=BG)
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
        try:
            self.root.attributes('-topmost', True)
            self.root.after(1400, lambda: self.root.attributes('-topmost', False))
        except tk.TclError:
            pass
        try:
            self.root.iconbitmap(default=str(self.app_dir / 'NOMIKO.ico'))
        except (tk.TclError, OSError):
            pass
        screen_w, screen_h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f'620x438+{max(0,(screen_w-620)//2)}+{max(0,(screen_h-438)//2)}')

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill='both', expand=True, padx=30, pady=24)

        top = tk.Frame(body, bg=BG)
        top.pack(fill='x')
        icon = tk.Canvas(top, width=46, height=46, bg=BG, highlightthickness=0)
        icon.pack(side='left', padx=(0, 12))
        _rounded(icon, 1, 1, 45, 45, 13, fill=ACCENT, outline='')
        icon.create_text(23, 23, text='N', fill=BG, font=('Segoe UI', 26, 'bold'))
        titles = tk.Frame(top, bg=BG)
        titles.pack(side='left')
        tk.Label(titles, text='NOMIKO', bg=BG, fg=TEXT,
                 font=('Segoe UI', 18, 'bold')).pack(anchor='w')
        tk.Label(titles, text='SECURE BROWSER UPDATE', bg=BG, fg=MUTED,
                 font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        tk.Label(top, text=f'STABLE  ·  {self.version}', bg=PANEL, fg=ACCENT,
                 font=('Segoe UI', 10, 'bold'), padx=14, pady=9).pack(side='right')

        tk.Frame(body, bg=BORDER, height=1).pack(fill='x', pady=(22, 22))
        self.heading = tk.Label(body, text='Preparing the update', bg=BG, fg=TEXT,
                                font=('Segoe UI', 21, 'bold'), anchor='w')
        self.heading.pack(fill='x')
        self.detail = tk.Label(body, text='NOMIKO has closed. Preparing the installer…',
                               bg=BG, fg=MUTED, font=('Segoe UI', 11), anchor='w')
        self.detail.pack(fill='x', pady=(8, 0))

        self.progress = tk.Canvas(body, height=13, bg=BG, highlightthickness=0)
        self.progress.pack(fill='x', pady=(28, 22))
        self.progress.bind('<Configure>', lambda event: self._draw_progress())
        self._draw_progress()

        phases = tk.Frame(body, bg=BG)
        phases.pack(fill='x')
        self.stage_labels = []
        for n, name in enumerate(STEPS):
            slot = tk.Frame(phases, bg=BG)
            slot.pack(side='left', expand=True, fill='x')
            label = tk.Label(slot, text=name, bg=BG, fg=MUTED,
                             font=('Segoe UI', 10), anchor='w')
            label.pack(anchor='w')
            self.stage_labels.append(label)
        self._set_phase(0)

        tk.Frame(body, bg=BORDER, height=1).pack(fill='x', pady=(30, 16))
        footer = tk.Frame(body, bg=BG)
        footer.pack(fill='x')
        self.note = tk.Label(footer, text='Your bookmarks, passwords and settings remain unchanged.',
                             bg=BG, fg=MUTED, font=('Segoe UI', 10), anchor='w')
        self.note.pack(side='left')
        self.action = tk.Button(footer, text='Open NOMIKO', command=self._launch_browser,
                                bg=ACCENT, fg=BG, activebackground='#B7A5FF',
                                activeforeground=BG, relief='flat', bd=0,
                                font=('Segoe UI', 11, 'bold'), padx=16, pady=10,
                                cursor='hand2')
        self.close_button = tk.Button(footer, text='Close', command=self._on_close,
                                      bg=PANEL, fg=TEXT, activebackground=BORDER,
                                      activeforeground=TEXT, relief='flat', bd=0,
                                      font=('Segoe UI', 10), padx=12, pady=10,
                                      cursor='hand2')
        self._tick()

    def _set_phase(self, phase):
        self.phase = max(0, min(3, phase))
        for n, label in enumerate(self.stage_labels):
            label.configure(fg=SUCCESS if n < self.phase else
                                ACCENT if n == self.phase else MUTED)
        self._draw_progress()

    def _draw_progress(self):
        c = self.progress
        c.delete('all')
        w = max(100, c.winfo_width())
        _rounded(c, 0, 1, w, 12, 6, fill=BORDER, outline='')
        if self.completed:
            color = SUCCESS if self.result == 0 else ERROR
            _rounded(c, 0, 1, w if self.result == 0 else w * 0.72, 12, 6,
                     fill=color, outline='')
            return
        # Each completed phase fills a real quarter of the track. The
        # moving highlight means installing, not a fabricated percentage.
        base = min(w-1, (w * self.phase) / 4)
        if base > 8:
            _rounded(c, 0, 1, base, 12, 6, fill=ACCENT, outline='')
        track = (w / 4)
        start = min(w-15, base + (self.animation / 100) * track)
        stop = min(w, start + max(24, track * 0.38))
        _rounded(c, max(0, start), 1, stop, 12, 6, fill='#D4CAFF', outline='')

    def _tick(self):
        if not self.root.winfo_exists():
            return
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == 'status':
                    _, step, message = event
                    names = {'closing': 0, 'verifying': 1, 'installing': 2,
                             'complete': 3, 'error': self.phase}
                    self._set_phase(names.get(step, 0))
                    self.heading.configure(text={
                        'closing': 'Closing background tasks',
                        'verifying': 'Checking update files',
                        'installing': 'Installing NOMIKO',
                        'complete': 'Update complete',
                        'error': 'Could not finish update',
                    }.get(step, 'Updating NOMIKO'))
                    self.detail.configure(text=message, fg=ERROR if step == 'error' else MUTED)
                elif event[0] == 'done':
                    self.completed = True
                    self.result = int(event[1])
                    if self.result == 0:
                        self._set_phase(3)
                        self.heading.configure(text='NOMIKO is up to date', fg=TEXT)
                        self.detail.configure(text=f'Version {self.version} installed successfully.',
                                              fg=SUCCESS)
                        self.action.pack(side='right')
                    else:
                        self.heading.configure(text='Update could not finish', fg=TEXT)
                        self.note.configure(text='Previous browser files are preserved when rollback succeeds.')
                    self.close_button.pack(side='right', padx=(0, 10))
                    self._draw_progress()
        except Empty:
            pass
        if not self.completed:
            self.animation = (self.animation + 5) % 100
            self._draw_progress()
        self.root.after(65, self._tick)

    def _background(self):
        try:
            result = self.worker(lambda step, message: self.events.put(('status', step, message)))
        except Exception as exc:
            self.events.put(('status', 'error', str(exc)))
            result = 10
        self.events.put(('done', result))

    def _launch_browser(self):
        if not self.completed or self.result != 0:
            return
        exe = self.app_dir / 'NOMIKO.exe'
        try:
            subprocess.Popen([str(exe)], cwd=str(self.app_dir), close_fds=True)
        except OSError as exc:
            self.heading.configure(text='Cannot start NOMIKO')
            self.detail.configure(text=str(exc), fg=ERROR)
            return
        self.root.destroy()

    def _on_close(self):
        # Do not let the user close the window mid-swap, leaving a half-step.
        if self.completed:
            self.root.destroy()

    def run(self):
        threading.Thread(target=self._background, daemon=True, name='NOMIKO Installer').start()
        self.root.mainloop()
        return self.result


def run_update_window(worker, *, app_dir, installer):
    return UpdateWindow(worker, app_dir=app_dir, installer=installer).run()


def self_check() -> int:
    """Quick packaged Tk/Tcl render and task handoff test for Windows CI."""
    def simulated(report):
        report('verifying', 'Checking the update package')
        time.sleep(0.12)
        report('installing', 'Applying the update')
        time.sleep(0.12)
        report('complete', 'Updater interface is working')
        return 0
    try:
        window = UpdateWindow(simulated, app_dir=Path.cwd(),
                              installer=Path('NOMIKO-Setup-0.9.15.exe'))
        state = {'passed': False}
        def finish():
            state['passed'] = window.completed and window.result == 0
            window.root.destroy()
        window.root.after(2300, finish)
        window.run()
        return 0 if state['passed'] else 3
    except Exception:
        return 4
