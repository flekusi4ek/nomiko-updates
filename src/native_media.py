"""NOMIKO's standalone FFmpeg-backed audio/video player.

This does not use Edge, WebView2 or an external browser. Qt Multimedia loads
its FFmpeg backend, independent from Qt WebEngine's Chromium codec flags.

Only explicit user actions open streams; SoundCloud extraction is restricted
to public track pages and never reads cookies, profiles or logins.
DRM-protected streams are not supported or bypassed.
"""
from __future__ import annotations

import ipaddress
from urllib.parse import urlsplit

from PySide6.QtCore import QThread, QUrl, Qt, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QPushButton,
                               QSlider, QVBoxLayout, QWidget)


def safe_remote_url(value: str) -> bool:
    """Do not let a web page route file:, loopback or internal IPs to FFmpeg."""
    if not isinstance(value, str) or len(value) > 2048:
        return False
    try:
        p = urlsplit(value)
        host = (p.hostname or '').lower().strip('.')
        if p.scheme != 'https' or not host or p.username or p.password:
            return False
        if host == 'localhost' or host.endswith(('.localhost', '.local', '.internal')):
            return False
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            return '.' in host and all(c.isascii() and (c.isalnum() or c in '.-') for c in host)
        return address.is_global
    except (ValueError, UnicodeError):
        return False


def soundcloud_track_url(value: str) -> bool:
    if not safe_remote_url(value):
        return False
    u = urlsplit(value)
    host = (u.hostname or '').lower()
    if host != 'soundcloud.com' and not host.endswith('.soundcloud.com'):
        return False
    parts = [p for p in u.path.split('/') if p]
    # A public song permalink has exactly /artist/song, not /you/likes or sets.
    return (len(parts) == 2 and parts[0].lower() not in {
        'you', 'discover', 'search', 'settings', 'upload', 'stream', 'stations'
    } and parts[1].lower() not in {'sets', 'albums', 'likes', 'tracks', 'reposts'})


def normalize_media_source(source: str, kind: str) -> bool:
    return soundcloud_track_url(source) if kind == 'soundcloud' else (
        kind == 'direct' and safe_remote_url(source))


def select_audio_url(info) -> str:
    """Take an extractor's selected public audio URL without downloading it."""
    if not isinstance(info, dict):
        return ''
    url = info.get('url')
    if safe_remote_url(url):
        return url
    formats = info.get('requested_formats') or info.get('formats') or []
    for f in reversed(formats):
        if isinstance(f, dict) and safe_remote_url(f.get('url')) and f.get('acodec') != 'none':
            return f['url']
    return ''


class PublicSoundCloudResolver(QThread):
    ready = Signal(str)
    failed = Signal(str)

    def __init__(self, permalink: str, parent=None):
        super().__init__(parent)
        self.permalink = permalink

    def run(self):
        if not soundcloud_track_url(self.permalink):
            self.failed.emit('Invalid SoundCloud song link.')
            return
        try:
            from yt_dlp import YoutubeDL
            # Public playback only. No cookies, account access, DRM bypass,
            # proxies, downloads, files or third-party playback services.
            with YoutubeDL({
                'format': 'bestaudio/best',
                'noplaylist': True,
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': 14,
                'retries': 1,
            }) as client:
                info = client.extract_info(self.permalink, download=False)
            source = select_audio_url(info)
            if not source:
                raise ValueError('This song does not provide an accessible public stream.')
            self.ready.emit(source)
        except Exception as exc:
            # Track titles and signed media URLs are never written to disk.
            self.failed.emit(
                'Could not open this song. It may require a SoundCloud account, '
                'be region-restricted or use a protected stream. '
                + str(exc)[:170])


class NativeMediaDialog(QDialog):
    """Responsive native media player; extraction happens off the UI thread."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('NOMIKO · Media Player')
        self.resize(760, 540)
        self.setMinimumSize(520, 300)
        self.setStyleSheet("""
            QDialog,QWidget {background:#151720;color:#EAEDF7;font-family:'Segoe UI';}
            QLabel {background:transparent;}
            QPushButton {border:0;background:#333748;color:#F3F0FF;
                         border-radius:9px;padding:10px 18px;font-weight:600;}
            QPushButton:hover {background:#49445D;}
            QPushButton#play {background:#A18AFF;color:#101019;}
            QSlider::groove:horizontal {height:5px;border-radius:2px;background:#414253;}
            QSlider::handle:horizontal {height:14px;width:14px;margin:-5px 0;
                                        background:#A18AFF;border-radius:7px;}
        """)
        self._resolver = None
        self.audio = QAudioOutput(self)
        self.audio.setVolume(0.70)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.audio)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 17, 20, 16)
        layout.setSpacing(12)
        title = QLabel('NOMIKO  /  MEDIA PLAYER')
        title.setStyleSheet('color:#AB9BFC;font-weight:700;font-size:13px;')
        layout.addWidget(title)
        self.video = QVideoWidget(self)
        self.video.setMinimumHeight(170)
        self.video.setStyleSheet('background:#090A10;border-radius:10px;')
        self.player.setVideoOutput(self.video)
        layout.addWidget(self.video, 1)
        self.video.hide()
        self.status = QLabel('Ready')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        row = QHBoxLayout()
        self.toggle = QPushButton('Pause')
        self.toggle.setObjectName('play')
        self.toggle.clicked.connect(self.toggle_playback)
        row.addWidget(self.toggle)
        self.seek = QSlider(Qt.Orientation.Horizontal)
        self.seek.setRange(0, 0)
        self.seek.sliderReleased.connect(self._seek)
        row.addWidget(self.seek, 1)
        self.time = QLabel('00:00 / 00:00')
        row.addWidget(self.time)
        layout.addLayout(row)
        volume_row = QHBoxLayout()
        volume_row.addWidget(QLabel('Volume'))
        volume = QSlider(Qt.Orientation.Horizontal)
        volume.setRange(0, 100)
        volume.setValue(70)
        volume.setMaximumWidth(190)
        volume.valueChanged.connect(lambda n: self.audio.setVolume(n / 100.0))
        volume_row.addWidget(volume)
        volume_row.addStretch()
        close = QPushButton('Close player')
        close.clicked.connect(self.close)
        volume_row.addWidget(close)
        layout.addLayout(volume_row)
        self.player.durationChanged.connect(self._duration)
        self.player.positionChanged.connect(self._position)
        self.player.hasVideoChanged.connect(self._video_state)
        self.player.playbackStateChanged.connect(self._playback_state)
        self.player.errorOccurred.connect(self._error)

    def _duration(self, duration):
        self.seek.setMaximum(max(0, duration))

    def _position(self, pos):
        if not self.seek.isSliderDown():
            self.seek.setValue(pos)
        self.time.setText(f'{self._clock(pos)} / {self._clock(self.player.duration())}')

    @staticmethod
    def _clock(milliseconds):
        secs = max(0, int(milliseconds) // 1000)
        return f'{secs // 60:02d}:{secs % 60:02d}'

    def _video_state(self, value):
        self.video.setVisible(bool(value))

    def _seek(self):
        self.player.setPosition(self.seek.value())

    def _playback_state(self, state):
        self.toggle.setText('Pause' if state == QMediaPlayer.PlaybackState.PlayingState else 'Play')

    def _error(self, error, text):
        if error != QMediaPlayer.Error.NoError:
            self.status.setText('Playback failed: ' + str(text)[:240] +
                                '. The source may be unavailable, protected or incompatible.')

    def toggle_playback(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def open_source(self, source, kind='direct'):
        if not normalize_media_source(source, kind):
            self.status.setText('Only public HTTPS media URLs or SoundCloud song links are supported.')
            return False
        if self._resolver is not None:
            try:
                if self._resolver.isRunning():
                    self.status.setText('Finishing the previous song lookup…')
                    self.show()
                    return False
            except RuntimeError:
                self._resolver = None
        self.player.stop()
        self.setWindowTitle('NOMIKO · ' + ('SoundCloud' if kind == 'soundcloud' else 'Media Player'))
        self.status.setText('Opening media…')
        if kind == 'soundcloud':
            self._resolver = PublicSoundCloudResolver(source, self)
            self._resolver.ready.connect(self._start_playback)
            self._resolver.failed.connect(self.status.setText)
            worker = self._resolver
            worker.finished.connect(lambda: setattr(self, '_resolver', None))
            worker.finished.connect(worker.deleteLater)
            worker.start()
        else:
            self._start_playback(source)
        self.show()
        self.raise_()
        self.activateWindow()
        return True

    def _start_playback(self, source):
        if not safe_remote_url(source):
            self.status.setText('Rejected an unsafe media stream URL.')
            return
        self.status.setText('Playing with Qt Multimedia / FFmpeg…')
        self.player.setSource(QUrl(source))
        self.player.play()

    def closeEvent(self, event):  # noqa: N802
        self.player.stop()
        # The worker owns only its network extraction, never a Qt QWidget.
        if self._resolver is not None and self._resolver.isRunning():
            event.ignore()
            self.status.setText('Finishing stream lookup before closing…')
            self._resolver.finished.connect(self.close)
            return
        super().closeEvent(event)
