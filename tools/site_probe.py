"""Windows QtWebEngine probe for a real Technical City page.

No account, cookies, browser history or user data is required; the whole
profile is isolated to a temporary folder on the CI machine.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
args = argparse.ArgumentParser()
args.add_argument('--allow-site', action='store_true')
args = args.parse_args()
os.environ['APPDATA'] = tempfile.mkdtemp(prefix='nomiko-site-probe-')
from src.storage import Store
settings = Store()
settings.settings.update({
    'updates_auto_check': False, 'restore_tabs': False, 'graphics_mode': 'compatibility',
    'block_exceptions': ['technical.city'] if args.allow_site else [],
    'tracker_blocking': True, 'ad_blocking': True,
})
settings.save_settings()
from src.rendering import configure_webengine
configure_webengine(settings.settings)
from PySide6.QtCore import QTimer, QUrl
from PySide6.QtWidgets import QApplication
from src.ui import BrowserWindow, BrowserView

app = QApplication([])
app.windows = []
window = BrowserWindow(private=True)
app.windows.append(window)
window.resize(1200, 800)
window.show()
url = 'https://technical.city/ru/can-i-run-it'
view = window.new_tab(url)
results = {'url': url, 'mode': 'allowlisted' if args.allow_site else 'normal', 'loaded': None}
view.loadFinished.connect(lambda ok: results.update(loaded=bool(ok)))
view.loadStarted.connect(lambda: print('started navigation', flush=True))


def snapshot():
    script = r"""(() => {
        let body=document.body;
        const t=(body?.innerText||'').trim();
        let b=body?.getBoundingClientRect();
        return {
            url:location.href, state:document.readyState,
            title:document.title, text_length:t.length, text:t.slice(0,260),
            tags:document.getElementsByTagName('*').length,
            body_color:body?getComputedStyle(body).backgroundColor:'',
            body_rect:b?[b.width,b.height]:null,
            visible_count:[...document.querySelectorAll('h1,p,a,button,main')]
                 .filter(el=>{let r=el.getBoundingClientRect();let s=getComputedStyle(el);return r.width>0&&r.height>0&&s.visibility!='hidden'&&s.display!='none'}).length
        };
    })()"""
    def received(data):
        results['dom'] = data
        image = view.grab().toImage()
        if not image.isNull():
            colors=set()
            for x in range(6):
                for y in range(6):
                    col=image.pixelColor(int((x+0.5)/6*image.width()),
                                         int((y+0.5)/6*image.height()))
                    colors.add((col.red(),col.green(),col.blue()))
            results['pixels_unique_sampled'] = len(colors)
            results['center_pixel'] = [
                image.pixelColor(image.width()//2,image.height()//2).red(),
                image.pixelColor(image.width()//2,image.height()//2).green(),
                image.pixelColor(image.width()//2,image.height()//2).blue()
            ]
        results['blocked'] = window.interceptor.counts()
        print('TECHNICAL_CITY_DIAG',json.dumps(results,ensure_ascii=False),flush=True)
        app.quit()
    view.page().runJavaScript(script, received)

QTimer.singleShot(18000, snapshot)
QTimer.singleShot(26000, lambda: app.exit(2))
sys.exit(app.exec())
