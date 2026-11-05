"""Site-scoped media compatibility without globally disabling autoplay protection."""


def is_soundcloud_host(host: str) -> bool:
    host = str(host or '').lower().rstrip('.')
    return host == 'soundcloud.com' or host.endswith('.soundcloud.com')


def playback_requires_gesture(autoplay_guard: bool, scheme: str, host: str) -> bool:
    """Allow SoundCloud media players to start while preserving other sites' guard."""
    soundcloud = str(scheme).lower() in ('http', 'https') and is_soundcloud_host(host)
    return bool(autoplay_guard) and not soundcloud


def missing_soundcloud_codecs(probe) -> bool:
    """Do not report codec failure if the JS diagnostic itself failed."""
    return isinstance(probe, dict) and not any(
        bool(probe.get(codec)) for codec in ('mp3', 'aac', 'mse_aac'))
