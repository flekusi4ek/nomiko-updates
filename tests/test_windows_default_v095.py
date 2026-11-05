"""Offline regressions for NOMIKO Windows default browser / minimal UI."""
from pathlib import Path
import tempfile
import unittest

from src.windows_integration import launch_target
from src.storage import DEFAULT_SETTINGS, TOOLBAR_ITEMS, MENU_ITEMS
from src.i18n import tr
from src.update_trust import CURRENT_VERSION

ROOT = Path(__file__).resolve().parents[1]


class ExternalLaunchTests(unittest.TestCase):
    def test_http_https_passed_by_windows(self):
        self.assertEqual(launch_target(['https://example.org/path?x=1']),
                         'https://example.org/path?x=1')
        self.assertEqual(launch_target(['http://example.org']), 'http://example.org')

    def test_invalid_and_special_links_blocked(self):
        for value in ('javascript:alert(1)', 'data:text/html,hi',
                      'file:///C:/secrets.txt', '--no-sandbox',
                      'https://username:password@example.org',
                      'https://', 'microsoft-edge:https://example.org'):
            with self.subTest(value=value):
                self.assertIsNone(launch_target([value]))

    def test_local_html_only(self):
        with tempfile.TemporaryDirectory() as folder:
            html = Path(folder) / 'index.html'
            html.write_text('<title>NOMIKO</title>', encoding='utf-8')
            self.assertEqual(launch_target([str(html)]), html.resolve().as_uri())
            secret = Path(folder) / 'data.txt'
            secret.write_text('not HTML', encoding='utf-8')
            self.assertIsNone(launch_target([str(secret)]))


class WindowsRegistrationTests(unittest.TestCase):
    def test_default_apps_registration(self):
        source = (ROOT / 'installer/NOMIKO.nsi').read_text(encoding='utf-8')
        for text in ('Software\\RegisteredApplications', 'NOMIKO.HTTP',
                     'NOMIKO.HTTPS', 'NOMIKO.HTML', 'UrlAssociations',
                     'FileAssociations', '"http"', '"https"', '".html"', '".htm"'):
            with self.subTest(text=text):
                self.assertIn(text, source)
        self.assertIn('DeleteRegValue HKCU', source)
        self.assertNotIn('UserChoice', source)
        self.assertIn('SHChangeNotify', source)

    def test_browser_responds_to_external_link(self):
        main = (ROOT / 'main.py').read_text()
        self.assertIn('launch_target(sys.argv[1:])', main)
        self.assertIn('window.open_url(requested)', main)
        self.assertIn('show_default_browser_settings', (ROOT / 'src/ui.py').read_text())

    def test_version(self):
        self.assertEqual(CURRENT_VERSION, '0.9.10')
        self.assertEqual((ROOT / '.github/release-request.txt').read_text().strip(), 'PUBLISH v0.9.10-alpha')


class MinimalUiTests(unittest.TestCase):
    def test_toolbar_no_private_button(self):
        self.assertNotIn('private', TOOLBAR_ITEMS)
        code = (ROOT / 'src/ui.py').read_text()
        self.assertNotIn('self.private_btn', code)
        self.assertIn("('New private window', 'Ctrl+Shift+N'", code)

    def test_downloads_session_icon_and_saved_history(self):
        code = (ROOT / 'src/ui.py').read_text()
        self.assertIn("(key != 'download' or bool(self.downloads))", code)
        self.assertIn('self.download_btn.setVisible', code)
        self.assertIn('self.store.record_download(', code)
        settings = (ROOT / 'src/settings_page.py').read_text()
        self.assertIn('Open downloads folder', settings)
        self.assertIn('Clear download history (keep files)', settings)

    def test_minimal_tabs_and_configurable_address(self):
        code = (ROOT / 'src/ui.py').read_text()
        self.assertIn('def set_density(self, density):', code)
        self.assertIn('self.address.setMaximumWidth(', code)
        self.assertEqual(DEFAULT_SETTINGS['tab_density'], 'slim')
        self.assertEqual(DEFAULT_SETTINGS['address_width'], 'balanced')

    def test_menu_keeps_working_actions(self):
        code = (ROOT / 'src/ui.py').read_text()
        self.assertIn("tools = menu.addMenu(self.t('Tools'))", code)
        self.assertIn('show_update_center', code)
        self.assertIn('show_main_menu', code)
        self.assertNotIn('private_window', MENU_ITEMS)

    def test_settings_search_all_controls(self):
        source = (ROOT / 'src/settings_page.py').read_text()
        self.assertIn('self.root.addWidget(self.rail, 0)', source)
        self.assertIn('self.root.addWidget(self.pages, 1)', source)
        self.assertIn('for cls in (QLabel, QCheckBox, QPushButton)', source)
        self.assertIn('Make NOMIKO default browser', source)

    def test_primary_language_buttons(self):
        for lang in ('uk','ru','pl','de'):
            for key in ('Make NOMIKO default browser', 'Address bar width',
                        'Open downloads folder', 'Clear download history (keep files)',
                        'Manage bookmarks and folders', 'Open Update Center'):
                with self.subTest(lang=lang, key=key):
                    self.assertNotEqual(tr(key, lang), key)
