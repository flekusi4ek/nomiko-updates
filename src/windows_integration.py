"""Windows 11 default-browser integration and safe external launch targets.

Association registration is done by the NSIS installer. This module only
opens Microsoft's UI and validates a URL/file supplied to NOMIKO at startup.
"""
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlsplit


def launch_target(arguments) -> str | None:
    """Accept a Windows shell-provided web URL or explicitly opened HTML file."""
    for raw in arguments:
        if not isinstance(raw, str) or not raw or len(raw) > 8192:
            continue
        value = raw.strip()
        try:
            url = urlsplit(value)
        except ValueError:
            continue
        if url.scheme.lower() in ('http', 'https') and url.hostname and not url.username and not url.password:
            return value
        if value.startswith('-') or '://' in value:
            continue
        candidate = Path(value)
        if candidate.suffix.lower() not in ('.htm', '.html'):
            continue
        try:
            if candidate.is_file():
                return candidate.resolve().as_uri()
        except (OSError, ValueError):
            pass
    return None


def open_windows_default_apps() -> bool:
    """Let the USER choose NOMIKO: never overwrite UserChoice registry keys."""
    if os.name != 'nt':
        return False
    try:
        os.startfile('ms-settings:defaultapps')
        return True
    except OSError:
        return False
