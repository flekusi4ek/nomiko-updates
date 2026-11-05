"""NOMIKO desktop browser (Windows 11)."""
from pathlib import Path
import os
import sys
from PySide6.QtGui import QIcon, QColor, QPalette
from PySide6.QtWidgets import QApplication
from src.windows_integration import launch_target
from src.storage import Store
from src.theme_background import page_background

def icon_path() -> Path:
    bundle = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
    return bundle / 'assets' / 'NOMIKO.ico'

def main():
    # Windows CI and troubleshooting: imports the native Qt WebEngine modules
    # without opening a full browser window or contacting any website.
    if '--self-check' in sys.argv:
        # The packaged windowed exe has no visible stderr. Persist the *actual*
        # traceback so CI can diagnose DLL/linker errors instead of guessing.
        try:
            from PySide6.QtWebEngineCore import QWebEngineProfile
            from PySide6.QtWebEngineWidgets import QWebEngineView
            from src.ui import BrowserWindow
            assert QWebEngineProfile and QWebEngineView and BrowserWindow
        except BaseException:
            import tempfile
            import traceback
            try:
                (Path(tempfile.gettempdir()) / 'NOMIKO-startup-diagnostic.txt').write_text(
                    traceback.format_exc(), encoding='utf-8')
            except OSError:
                pass
            return 23
        return 0
    from src.ui import BrowserWindow
    if os.name == 'nt':
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('NOMIKO.Browser')
        except (AttributeError, OSError):
            pass
    app = QApplication(sys.argv)
    # Set the native window background before constructing/showing BrowserWindow:
    # avoids a white Win11/Qt flash while WebEngine initializes.
    initial_bg = QColor(page_background(Store().settings))
    palette = app.palette()
    palette.setColor(QPalette.ColorRole.Window, initial_bg)
    palette.setColor(QPalette.ColorRole.Base, initial_bg)
    app.setPalette(palette)
    app.setApplicationName('NOMIKO')
    app.setOrganizationName('NOMIKO')
    app.setWindowIcon(QIcon(str(icon_path())))
    app.windows = []
    window = BrowserWindow()
    window.setWindowIcon(app.windowIcon())
    app.windows.append(window)
    window.show()
    requested = launch_target(sys.argv[1:])
    if requested:
        # Windows invokes the registered browser with a URL as argument.
        window.open_url(requested)
    sys.exit(app.exec())

if __name__ == '__main__':
    sys.exit(main())
