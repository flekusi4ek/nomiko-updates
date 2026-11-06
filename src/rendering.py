"""Conservative graphics startup policy for Windows Qt WebEngine.

Qt documents --disable-gpu as a software-rendering fallback for black/blank
pages on machines with broken graphics backends. This setting is applied before
Qt WebEngine is imported; changing it requires a browser restart.
"""
from __future__ import annotations
import os

MODES = ('compatibility', 'hardware')


def rendering_mode(settings):
    value = settings.get('graphics_mode', 'compatibility')
    return value if value in MODES else 'compatibility'


def chromium_flags(mode, existing=''):
    """Keep existing safe flags while adding Qt's documented software fallback."""
    tokens = str(existing).split()
    if mode != 'hardware' and '--disable-gpu' not in tokens:
        tokens.append('--disable-gpu')
    return ' '.join(tokens)


def configure_webengine(settings, environ=None):
    environ = os.environ if environ is None else environ
    mode = rendering_mode(settings)
    flags = chromium_flags(mode, environ.get('QTWEBENGINE_CHROMIUM_FLAGS', ''))
    if flags:
        environ['QTWEBENGINE_CHROMIUM_FLAGS'] = flags
    return mode
