"""Send explicitly opened Discord server invites to the installed desktop app.

Only a genuine Discord invite URL and a user-initiated main-frame navigation
may invoke the Windows-registered Discord URL protocol. NOMIKO never reads
Discord credentials/cookies or contacts the Discord RPC port.
"""
from __future__ import annotations

import os
import re
from urllib.parse import urlsplit

_INVITE_CODE = re.compile(r'[A-Za-z0-9_-]{2,64}\Z')
_INVITE_HOSTS = frozenset({
    'discord.gg', 'www.discord.gg',
    'discord.com', 'www.discord.com',
    'discordapp.com', 'www.discordapp.com',
    'canary.discord.com', 'ptb.discord.com',
})


def discord_invite_code(value: str) -> str | None:
    """Accept only real invite pages, never lookalike domains or OAuth links."""
    if not isinstance(value, str) or len(value) > 2048:
        return None
    try:
        u = urlsplit(value.strip())
        host = (u.hostname or '').lower().rstrip('.')
        if (u.scheme.lower() not in ('http', 'https')
                or host not in _INVITE_HOSTS or u.username or u.password
                or u.port not in (None, 80, 443)):
            return None
        parts = u.path.strip('/').split('/')
        if host in ('discord.gg', 'www.discord.gg'):
            if len(parts) != 1:
                return None
            code = parts[0]
        else:
            if len(parts) != 2 or parts[0].lower() != 'invite':
                return None
            code = parts[1]
        return code if _INVITE_CODE.fullmatch(code) else None
    except (ValueError, UnicodeError):
        return None


def discord_protocol_registered() -> bool:
    """Use the user's OS-selected handler; never search, launch or trust EXEs."""
    if os.name != 'nt':
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, 'discord') as key:
            winreg.QueryValueEx(key, 'URL Protocol')
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT,
                            r'discord\shell\open\command') as key:
            command, _ = winreg.QueryValueEx(key, None)
        return bool(str(command).strip())
    except (OSError, ImportError, ValueError):
        return False


def should_open_in_discord(value: str, navigation_type, *,
                           main_frame=True, enabled=True,
                           restoring_session=False) -> bool:
    """Only link-clicks/typed URLs; never hidden iframes or JS redirects."""
    kind = getattr(navigation_type, 'value', navigation_type)
    return bool(
        enabled and main_frame and not restoring_session
        and kind in (0, 1)
        and discord_invite_code(value)
    )


def open_discord_invite(value: str) -> bool:
    """Open a validated invite in the registered Discord desktop application."""
    code = discord_invite_code(value)
    if not code or not discord_protocol_registered():
        return False
    try:
        # A fixed scheme and validated token: no shell, script or arbitrary URL.
        os.startfile('discord://-/invite/' + code)
        return True
    except (OSError, AttributeError):
        return False
