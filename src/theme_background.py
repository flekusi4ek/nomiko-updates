"""NOMIKO theme colors used before the first Qt/WebEngine frame is painted.

Keep the startup canvas consistent with BrowserWindow.apply_theme.
"""


def page_background(settings) -> str:
    theme = settings.get('theme', 'dark')
    if theme == 'light':
        return '#F6F7FA'
    if theme == 'midnight':
        return '#11131A'
    return '#292C33'


def apply_page_background(view, settings):
    """Eliminate WebEngine's default white document-loading background."""
    from PySide6.QtGui import QColor, QPalette
    color = QColor(page_background(settings))
    page = view.page()
    if page is not None:
        page.setBackgroundColor(color)
    palette = view.palette()
    palette.setColor(QPalette.ColorRole.Window, color)
    palette.setColor(QPalette.ColorRole.Base, color)
    view.setPalette(palette)
    view.setAutoFillBackground(True)
