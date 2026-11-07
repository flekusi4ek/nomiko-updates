"""Opt-in SoundCloud diagnostics. No track URLs, cookies or logins are collected."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QMessageBox
from .media_compat import is_soundcloud_host


def playback_summary(result, blocked, allowlisted, muted):
    lines = []
    if muted:
        lines.append('This NOMIKO tab is muted.')
    if isinstance(result, dict):
        for name, key in (('MP3', 'mp3'), ('AAC', 'aac'), ('Opus', 'opus')):
            lines.append(f'{name}: ' + ('supported' if result.get(key) else 'not supported'))
        descriptions = {1: 'playback interrupted', 2: 'network error',
                        3: 'decode error', 4: 'unsupported media source'}
        error_codes = result.get('errors', [])
        if isinstance(error_codes, list) and error_codes:
            lines.append('Media errors: ' + ', '.join(
                descriptions.get(code, 'unknown') for code in error_codes[:4]))
        else:
            lines.append('No visible media error detected (the player may use hidden audio).')
    else:
        lines.append('Audio check unavailable; reload the page and try again.')
    lines.append(f'SoundCloud-page requests blocked by NOMIKO this session: {blocked}')
    lines.append('SoundCloud site filter: ' + ('off' if allowlisted else 'on'))
    lines.append('If Likes fail, try Play in NOMIKO beside a public track. Private, region-blocked or protected tracks may be unavailable.')
    return '\n'.join(lines)


class SoundCloudHelpDialog(QDialog):
    def __init__(self, browser, view):
        super().__init__(browser)
        self.browser, self.view = browser, view
        self.setWindowTitle('SoundCloud · Playback help')
        self.resize(530, 380)
        self.setMinimumWidth(450)
        root = QVBoxLayout(self)
        description = QLabel(
            'If tracks in Likes do not play, first try a song directly on its '
            'track page. A track may also be unavailable because of region '
            'restrictions or a SoundCloud-side issue.\n\n'
            'This diagnostic runs locally and does not collect track titles, '
            'cookies, account data or streaming addresses.')
        description.setWordWrap(True)
        root.addWidget(description)
        self.summary = QLabel(
            'After attempting to play a liked track, click Check playback. '
            'You can keep this window open while using SoundCloud.')
        self.summary.setWordWrap(True)
        self.summary.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        root.addWidget(self.summary, 1)
        row = QHBoxLayout()
        check = QPushButton('Check playback')
        check.clicked.connect(self.check_playback)
        row.addWidget(check)
        close = QPushButton('Close')
        close.clicked.connect(self.close)
        row.addWidget(close)
        root.addLayout(row)
        self.allow = QPushButton()
        self.allow.clicked.connect(self.toggle_exception)
        root.addWidget(self.allow)
        self.update_button()

    def allowlisted(self):
        return 'soundcloud.com' in self.browser.store.settings.get('block_exceptions', [])

    def update_button(self):
        self.allow.setText(
            'Restore SoundCloud site protection' if self.allowlisted()
            else 'Allow SoundCloud requests (reduces protection on SoundCloud only)')

    def toggle_exception(self):
        exceptions = [s for s in self.browser.store.settings.get('block_exceptions', [])
                      if s != 'soundcloud.com']
        if not self.allowlisted():
            choice = QMessageBox.question(
                self, 'SoundCloud only',
                'Allow potentially blocked third-party requests from SoundCloud pages?\n'
                'This weakens blocking only when SoundCloud is the first party.\n'
                'You can restore protection using the same button.',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if choice != QMessageBox.StandardButton.Yes:
                return
            exceptions.append('soundcloud.com')
        self.browser.update_preference(block_exceptions=exceptions)
        self.update_button()
        self.summary.setText(
            'SoundCloud exception updated. Reload the Likes page, then try playing '
            'the affected track again. This does not unlock restricted songs.')

    def check_playback(self):
        if not is_soundcloud_host(self.view.url().host()):
            self.summary.setText('Navigate back to SoundCloud before checking audio.')
            return
        self.summary.setText('Checking playback capabilities…')
        js = """(() => {
            const el = document.createElement('audio');
            const elements = Array.from(document.querySelectorAll('audio, video')).slice(0, 8);
            return {
                mp3: Boolean(el.canPlayType('audio/mpeg')),
                aac: Boolean(el.canPlayType('audio/mp4; codecs="mp4a.40.2"')),
                opus: Boolean(el.canPlayType('audio/ogg; codecs="opus"')),
                errors: elements.filter(e => e.error).map(e => e.error.code)
            };
        })()"""
        def received(result):
            if not self.isVisible():
                return
            self.summary.setText(playback_summary(
                result, self.browser.interceptor.soundcloud_block_count(),
                self.allowlisted(), self.view.page().isAudioMuted()))
        self.view.page().runJavaScript(js, received)
