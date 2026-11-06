"""NOMIKO desktop browser (Windows 11)."""
from pathlib import Path
import os
import sys
from PySide6.QtGui import QIcon, QColor, QPalette
from PySide6.QtWidgets import QApplication
from src.windows_integration import launch_target
from src.storage import Store
from src.theme_background import page_background
from src.rendering import configure_webengine

def icon_path() -> Path:
    bundle = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
    return bundle / 'assets' / 'NOMIKO.ico'

def load_browser_window():
    """Use exactly the same native Qt import order in diagnostics and real startup."""
    import time
    for attempt in range(4):
        try:
            from PySide6.QtWebEngineCore import QWebEngineProfile
            from PySide6.QtWebEngineWidgets import QWebEngineView
            from src.ui import BrowserWindow
            assert QWebEngineProfile and QWebEngineView
            return BrowserWindow
        except ImportError as exc:
            if attempt == 3 or 'used by another process' not in str(exc).lower():
                raise
            # Windows antivirus/indexing can temporarily hold a freshly
            # installed DLL. Retry just the sharing-violation case.
            time.sleep((0.4, 0.8, 1.6)[attempt])


def write_startup_diagnostic():
    import tempfile
    import traceback
    try:
        (Path(tempfile.gettempdir()) / 'NOMIKO-startup-diagnostic.txt').write_text(
            traceback.format_exc(), encoding='utf-8')
    except OSError:
        pass


def main():
    # Apply the Qt WebEngine graphics backend before loading its native modules.
    configure_webengine(Store().settings)
    # CI and normal startup must exercise the exact same native DLL load path.
    if '--self-check' in sys.argv:
        try:
            load_browser_window()
        except BaseException:
            write_startup_diagnostic()
            return 23
        return 0
    try:
        BrowserWindow = load_browser_window()
    except ImportError:
        write_startup_diagnostic()
        if os.name == 'nt':
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(
                    None,
                    'NOMIKO could not load the Qt WebEngine libraries. Close any remaining NOMIKO processes or restart Windows, then run the latest installer. A diagnostic file was saved to the TEMP folder.',
                    'NOMIKO startup error', 0x10)
            except (OSError, AttributeError):
                pass
        return 24
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
