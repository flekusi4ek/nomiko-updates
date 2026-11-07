"""Offline HTML5 codec probe for NOMIKO's actual Qt WebEngine (no Edge).

Runs locally, stores no user data, and does not contact external websites.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ['APPDATA'] = tempfile.mkdtemp(prefix='nomiko-codec-probe-')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.storage import Store
s = Store()
s.settings.update({'updates_auto_check': False, 'restore_tabs': False,
                   'graphics_mode': 'compatibility'})
s.save_settings()
from src.rendering import configure_webengine
configure_webengine(s.settings)
from PySide6.QtCore import QTimer, QUrl
from PySide6.QtWidgets import QApplication
from src.ui import BrowserWindow

app = QApplication([])
app.windows = []
w = BrowserWindow()
app.windows.append(w)
w.resize(1000, 600)
w.show()
v = w.new_tab()
v.setHtml('<!doctype html><html><head><meta charset="utf-8"><title>Media support</title></head><body>Codec test</body></html>', QUrl('about:blank'))

js = r"""(() => {
  const a=document.createElement('audio'),v=document.createElement('video');
  const tests={
    mp3:a.canPlayType('audio/mpeg'),
    aac:a.canPlayType('audio/mp4; codecs="mp4a.40.2"'),
    ogg_opus:a.canPlayType('audio/ogg; codecs="opus"'),
    h264:v.canPlayType('video/mp4; codecs="avc1.42E01E"'),
    webm_vp8:v.canPlayType('video/webm; codecs="vp8"'),
    media_source:!!window.MediaSource,
    mse_mp4:!!(window.MediaSource&&window.MediaSource.isTypeSupported('video/mp4; codecs="avc1.42E01E"')),
    mse_aac:!!(window.MediaSource&&window.MediaSource.isTypeSupported('audio/mp4; codecs="mp4a.40.2"'))
  };
  return tests;
})()"""
finished = False

def ready(ok):
    if not ok:
        print('NOMIKO_CODEC_PROBE FAILED: local HTML load error', flush=True)
        app.exit(2)
        return
    def result(data):
        global finished
        finished = True
        print('NOMIKO_CODEC_RESULTS=' + json.dumps(data,sort_keys=True), flush=True)
        app.exit(0)
    v.page().runJavaScript(js,result)

v.loadFinished.connect(ready)
# setHtml may have raced signal above, request again on event loop.
QTimer.singleShot(900, lambda: v.page().runJavaScript(js, lambda x: print('NOMIKO_CODEC_BACKUP=' + json.dumps(x), flush=True)))
QTimer.singleShot(10000, lambda: app.exit(0 if finished else 3))
sys.exit(app.exec())
