"""NOMIKO v0.9.13: right-aligned window controls and first-frame theme regression."""
import unittest
from pathlib import Path

from src.theme_background import page_background

ROOT = Path(__file__).resolve().parents[1]


class BackgroundTests(unittest.TestCase):
    def test_theme_canvas_presets(self):
        self.assertEqual(page_background({'theme': 'dark'}), '#292C33')
        self.assertEqual(page_background({'theme': 'midnight'}), '#11131A')
        self.assertEqual(page_background({'theme': 'light'}), '#F6F7FA')
        self.assertEqual(page_background({}), '#292C33')

    def test_webengine_background_before_navigation(self):
        src = (ROOT / 'src/ui.py').read_text(encoding='utf-8')
        page_start = src.index('class NomikoPage(QWebEnginePage)')
        page_end = src.index('    def acceptNavigationRequest', page_start)
        self.assertIn('self.setBackgroundColor(QColor(page_background', src[page_start:page_end])
        ctor_start = src.index('class BrowserView(QWebEngineView)')
        ctor_end = src.index('    def createWindow', ctor_start)
        self.assertIn('apply_page_background(self, browser.store.settings)', src[ctor_start:ctor_end])
        self.assertIn('apply_page_background(tab.left, settings)', src)
        self.assertIn('apply_page_background(tab.right, settings)', src)
        split = (ROOT / 'src/advanced_ui.py').read_text(encoding='utf-8')
        self.assertIn('apply_page_background(self.view, self.browser.store.settings)', split)

    def test_app_palette_before_first_show(self):
        main = (ROOT / 'main.py').read_text(encoding='utf-8')
        self.assertLess(main.index('app.setPalette(palette)'), main.index('window = BrowserWindow()'))
        self.assertLess(main.index('window = BrowserWindow()'), main.index('window.show()'))


class ToolbarTests(unittest.TestCase):
    def test_order_and_sizes(self):
        code = (ROOT / 'src/ui.py').read_text(encoding='utf-8')
        self.assertEqual(code.count("size=(36, 32)"), 3)
        self.assertIn('for button in (self.minimize_btn, self.maximize_btn, self.close_btn):', code)
        self.assertIn('quick_row.addWidget(self.bookmark_btn)', code)
        self.assertIn('quick_row.addWidget(self.menu_btn)', code)
        self.assertIn('bar.addWidget(self.quick_controls)', code)
        self.assertIn('bar.addWidget(self.window_controls)', code)
        self.assertIn('bar.addWidget(drag, 1)', code)
        self.assertIn("anchored = ('bookmark', 'menu')", code)
        self.assertNotIn('bar.insertWidget(0, self.window_controls)', code)

    def test_click_targets_and_glyphs_are_centered(self):
        code = (ROOT / 'src/ui.py').read_text(encoding='utf-8')
        self.assertIn('for button in (self.minimize_btn, self.maximize_btn, self.close_btn)', code)
        self.assertIn("painter.drawLine(QPointF(x-6, y), QPointF(x+6, y))", code)
        self.assertIn("painter.drawRect(int(x-6), int(y-6), 12, 12)", code)
        self.assertIn("r = 6 if g == 'close' else 4.5", code)
        self.assertIn('min-width:36px;max-width:36px;min-height:32px;max-height:32px', code)

    def test_shortcuts_and_other_customization_remain(self):
        src = (ROOT / 'src/ui.py').read_text(encoding='utf-8')
        self.assertIn('layout.insertWidget(position, widget', src)
        self.assertIn('widget.setVisible(key not in hidden', src)
        self.assertIn("'Ctrl+D'", src)
        self.assertIn('def show_main_menu(self)', src)


class ReleaseTests(unittest.TestCase):
    def test_release_version(self):
        from src.update_trust import CURRENT_VERSION
        self.assertEqual(CURRENT_VERSION, '0.9.13')
        self.assertEqual((ROOT / '.github/release-request.txt').read_text().strip(), 'PUBLISH v0.9.13')
