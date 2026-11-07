"""Conservative graphics startup policy for Windows Qt WebEngine.

Normal mode uses Qt/Chromium's GPU acceleration and built-in fallback.
Compatibility mode forces --disable-gpu only when explicitly selected. This
flag must be set before the first Qt WebEngine import, requiring a restart.
"""
from __future__ import annotations
import os

MODES = ('compatibility', 'hardware')


def rendering_mode(settings):
    value = settings.get('graphics_mode', 'hardware')
    return value if value in MODES else 'hardware'


def chromium_flags(mode, existing=''):
    """Keep existing safe flags while adding Qt's documented software fallback."""
    tokens = str(existing).split()
    if mode == 'compatibility' and '--disable-gpu' not in tokens:
        tokens.append('--disable-gpu')
    return ' '.join(tokens)


def configure_webengine(settings, environ=None):
    environ = os.environ if environ is None else environ
    mode = rendering_mode(settings)
    flags = chromium_flags(mode, environ.get('QTWEBENGINE_CHROMIUM_FLAGS', ''))
    if flags:
        environ['QTWEBENGINE_CHROMIUM_FLAGS'] = flags
    return mode
