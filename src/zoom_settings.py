"""Validation and defaults for global website zoom (no Qt imports)."""

ZOOM_LEVELS = (50, 67, 75, 80, 90, 100, 110, 120, 125, 133, 150, 170, 175, 200, 250, 300)


def zoom_percent(settings) -> int:
    try:
        value = int(settings.get('default_zoom', 100))
    except (ValueError, TypeError):
        return 100
    return value if value in ZOOM_LEVELS else 100


def zoom_text_only(settings) -> bool:
    return settings.get('zoom_text_only', False) is True
