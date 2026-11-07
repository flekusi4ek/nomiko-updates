"""Probe the native Windows QtWebView backend before enabling media tabs.

Windows QtWebView should use the system Edge WebView2 engine. Record actual
HTML5 codec support from the backend; never infer it from the module import.
"""
from __future__ import annotations
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ['APPDATA'] = tempfile.mkdtemp(prefix='nomiko-native-media-')
from PySide6.QtWebView import QWebView, QtWebView
QtWebView.initialize()
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PySide6.QtCore import QTimer, QUrl

app = QApplication([])
host = QWidget()
host.setWindowTitle('NOMIKO WebView2 media check')
host.resize(720, 420)
layout = QVBoxLayout(host)
view = QWebView()
layout.addWidget(QWidget.createWindowContainer(view, host))
host.show()
done = [False]
url = "data:text/html,<html><title>Media check</title><body style='background:#65439A;color:white'>NOMIKO Media Probe</body></html>"
view.setUrl(QUrl(url))
js = r"""(() => {
 const a=document.createElement('audio'),v=document.createElement('video');
 return JSON.stringify({
 title:document.title,
 mp3:a.canPlayType('audio/mpeg'),
 aac:a.canPlayType('audio/mp4; codecs="mp4a.40.2"'),
 h264:v.canPlayType('video/mp4; codecs="avc1.42E01E"'),
 webm:v.canPlayType('video/webm; codecs="vp8"'),
 ua:navigator.userAgent
 });
})()"""

def result(value):
    done[0] = True
    print("NOMIKO_NATIVE_MEDIA_CODECS", value, flush=True)
    app.quit()

def read():
    try:
        print("NOMIKO_NATIVE_BACKEND", str(view.httpUserAgentString()), flush=True)
        view.runJavaScript(js, result)
    except Exception as exc:
        print("NOMIKO_NATIVE_MEDIA_ERROR", type(exc).__name__, str(exc), flush=True)
        app.exit(2)

QTimer.singleShot(3000, read)
QTimer.singleShot(11000, lambda: app.exit(3) if not done[0] else None)
code = app.exec()
sys.exit(code)
