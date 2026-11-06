"""Windows GUI smoke: verifies real WebEngine pixels without mouse clicks.

Uses an isolated local profile and a vivid offline HTML document. It fails
if a new tab or an activated tab stays black, blank, or unpainted. Windows
CI should run this after building and before publishing a Stable release.
"""
from __future__ import annotations
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ['APPDATA'] = tempfile.mkdtemp(prefix='nomiko-smoke-profile-')

from src.storage import Store

store = Store()
store.settings.update({'updates_auto_check': False, 'restore_tabs': False,
                       'graphics_mode': 'compatibility'})
store.save_settings()
from src.rendering import configure_webengine
configure_webengine(store.settings)

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtWidgets import QApplication
from src.ui import BrowserWindow

app = QApplication([])
app.setApplicationName('NOMIKO Rendering Test')
app.windows = []
window = BrowserWindow()
app.windows.append(window)
window.resize(1100, 740)
window.show()
home = window.tabs.currentWidget()
tab = window.new_tab()
tab.setHtml(
    '<!doctype html><html><head><meta charset="utf-8"></head>'
    '<body style="margin:0;background:#d7e6fa;color:#202030">'
    '<div id="ready" style="background:#d7e6fa;height:100vh;padding:20px">'
    'NOMIKO OFFLINE RENDERING TEST</div></body></html>',
    QUrl('about:blank')
)
failures = []
samples = []


def check_pixels(stage):
    """Check that the center of the WebEngine viewport is visibly colored."""
    if window.current_view() is not tab or not tab.isVisible():
        failures.append(f'{stage}: requested tab is not visible')
        return
    image = tab.grab().toImage()
    if image.isNull() or image.width() < 300 or image.height() < 200:
        failures.append(f'{stage}: captured WebEngine viewport is empty')
        return
    positions = [(0.5, 0.5), (0.25, 0.5), (0.75, 0.7)]
    colors = [image.pixelColor(int(image.width() * x), int(image.height() * y))
              for x, y in positions]
    pixels = [(c.red(), c.green(), c.blue()) for c in colors]
    samples.append((stage, pixels))
    if not all(170 <= r <= 255 and 170 <= g <= 255 and 185 <= b <= 255
               for r, g, b in pixels):
        image.save(str(Path(tempfile.gettempdir()) / 'NOMIKO-black-tab-smoke.png'))
        failures.append(f'{stage}: expected light-blue content, got {pixels}')


def start_switching():
    check_pixels('new tab initial frame')
    window.tabs.setCurrentIndex(window.tabs.indexOf(home))
    QTimer.singleShot(160, activate_again)


def activate_again():
    window.tabs.setCurrentIndex(window.tabs.indexOf(tab))
    QTimer.singleShot(550, lambda: check_pixels('first reactivation'))
    QTimer.singleShot(1200, lambda: check_pixels('second reactivation'))
    QTimer.singleShot(2050, finish)


def finish():
    check_pixels('after idle')
    for stage, pixels in samples:
        print(f'{stage}: {pixels}', flush=True)
    if failures:
        for failure in failures:
            print('FAIL: ' + failure, flush=True)
    else:
        print('PASS: new tab paints immediately; switching does not leave black surface.', flush=True)
    app.exit(1 if failures else 0)


def timed_out():
    print('FAIL: GUI/WebEngine rendering smoke timed out.', flush=True)
    app.exit(2)


QTimer.singleShot(1500, start_switching)
QTimer.singleShot(16000, timed_out)
sys.exit(app.exec())
