"""NOMIKO v0.9.8: left-side button sizing and independent center alignment.

The right-side controls are intentionally identical to v0.9.7.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LeftToolbarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ui = (ROOT / 'src/ui.py').read_text(encoding='utf-8')
        cls.setup = cls.ui.split('    def _setup_ui(self):', 1)[1].split('    def _btn(', 1)[0]

    def test_left_navigation_all_28_square(self):
        for name in ('brand_btn', 'back_btn', 'next_btn', 'reload_btn',
                     'home_btn', 'download_btn'):
            with self.subTest(name=name):
                self.assertRegex(self.setup, rf'self\.{name}\s*=.*size=\(28, 28\)')

    def test_right_controls_unchanged(self):
        for name, glyph in (('minimize_btn','min'), ('maximize_btn','max'), ('close_btn','close')):
            with self.subTest(name=name):
                self.assertIn(
                    f"self.{name} = self._btn('{glyph}',", self.setup
                )
        self.assertEqual(self.setup.count('size=(36, 32)'), 3)
        self.assertIn('for button in (self.minimize_btn, self.maximize_btn, self.close_btn):', self.setup)
        self.assertIn('quick_row.addWidget(self.bookmark_btn)', self.setup)
        self.assertIn('quick_row.addWidget(self.menu_btn)', self.setup)
        self.assertIn('bar.addWidget(self.quick_controls)', self.setup)
        self.assertIn('bar.addWidget(self.window_controls)', self.setup)
        self.assertIn("size=(31, 31)", self.setup)  # only right-side bookmarks/menu

    def test_address_is_overlay_centered_on_entire_window(self):
        self.assertIn('self.address = QLineEdit(toolbar)', self.setup)
        self.assertNotIn('bar.addWidget(self.address)', self.setup)
        geom = self.ui.split('    def _center_address_bar(self):', 1)[1].split('    def _apply_toolbar(self):', 1)[0]
        self.assertIn('center_x = (toolbar.width() - width) // 2', geom)
        self.assertIn('right_start = self.quick_controls.geometry().left()', geom)
        self.assertIn('left_end = max((', geom)
        self.assertIn('self.address.setGeometry(x, y, width, self.address.height())', geom)
        self.assertIn('self.address.raise_()', geom)

    def test_custom_toolbar_order_does_not_move_center_or_right_group(self):
        layout = self.ui.split('    def _apply_toolbar(self):', 1)[1].split('    def _apply_bookmark_position(self):', 1)[0]
        self.assertIn("key == 'address'", layout)
        self.assertIn('QTimer.singleShot(0, self._center_address_bar)', layout)
        self.assertIn("anchored = ('bookmark', 'menu')", layout)
        self.assertIn('layout.insertWidget(position, widget)', layout)
        self.assertNotIn('layout.insertWidget(position, self.window_controls)', layout)

    def test_left_icons_centered(self):
        painter = self.ui.split('class IconButton(QToolButton):', 1)[1].split('class NomikoTabBar(QTabBar):', 1)[0]
        self.assertIn("tip = x + 7 * sign", painter)
        self.assertIn('painter.drawArc(int(x-7), int(y-7), 14, 14', painter)
        self.assertIn('font.setPointSize(16)', painter)
        self.assertNotIn("painter.translate(0, -2)", painter)


if __name__ == '__main__':
    unittest.main()
