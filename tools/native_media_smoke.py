"""Windows Qt Multimedia FFmpeg backend smoke: no Edge, no internet.

Tests the actual media backend by opening a short generated WAV audio file.
Also enumerates supported decode video formats/codecs for release diagnosis.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import struct
import sys
import tempfile
import wave

os.environ['QT_MEDIA_BACKEND'] = 'ffmpeg'
from PySide6.QtCore import QTimer, QUrl
from PySide6.QtMultimedia import QMediaFormat, QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import QApplication

app = QApplication([])
tmp = tempfile.TemporaryDirectory(prefix='nomiko-media-smoke-', ignore_cleanup_errors=True)
source = Path(tmp.name) / 'tone.wav'
with wave.open(str(source), 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(22050)
    samples = [int(700 * math.sin(2 * math.pi * 440 * i / 22050)) for i in range(22050)]
    w.writeframes(struct.pack('<' + 'h' * len(samples), *samples))

media_format = QMediaFormat()
video = [x.name for x in media_format.supportedVideoCodecs(QMediaFormat.ConversionMode.Decode)]
audio = [x.name for x in media_format.supportedAudioCodecs(QMediaFormat.ConversionMode.Decode)]
print('NOMIKO_NATIVE_CODECS=' + json.dumps({'video':video, 'audio':audio}), flush=True)
player = QMediaPlayer()
device = QAudioOutput()
player.setAudioOutput(device)
device.setVolume(0.0)
states = []
errors = []
player.mediaStatusChanged.connect(lambda state: states.append(state.name))
player.errorOccurred.connect(lambda err, desc: errors.append(str(desc)))
player.setSource(QUrl.fromLocalFile(str(source)))
player.play()

def finish():
    print('NOMIKO_MEDIA_SMOKE=' + json.dumps(
        {'statuses':states, 'errors':errors,
         'duration':player.duration(), 'position':player.position()}), flush=True)
    success = (any(s in ('LoadedMedia', 'BufferedMedia', 'EndOfMedia') for s in states)
               and 'H264' in video and 'MP3' in audio and 'AAC' in audio)
    if not success:
        print('Media backend failed to load a valid offline WAV file.', flush=True)
    app.exit(0 if success else 2)

QTimer.singleShot(4500, finish)
QTimer.singleShot(8500, lambda: app.exit(3))
try:
    result = app.exec()
finally:
    player.stop()
    tmp.cleanup()
sys.exit(result)
