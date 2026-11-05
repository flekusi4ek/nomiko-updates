"""Regression checks for the NOMIKO v0.9.10 search chooser and bookmark rail."""
import unittest
from pathlib import Path

from src.home import _form, render_home, render_search_results
from src.bookmark_visibility import has_bookmark_toolbar_content

ROOT = Path(__file__).resolve().parents[1]


class SearchPickerTests(unittest.TestCase):
    def test_picker_left_of_input(self):
        form = _form('Google', visible_engines=['DuckDuckGo', 'Google'])
        self.assertIn('class="engine-picker"', form)
        self.assertLess(form.index('class="engine-picker"'), form.index('name="q"'))
        self.assertEqual(form.count('class="engine-picker"'), 1)
        self.assertIn('class="engine-menu"', form)

    def test_single_provider_hides_chooser(self):
        for provider in ('DuckDuckGo', 'NOMIKO Search', 'Google'):
            with self.subTest(provider=provider):
                form = _form(provider, visible_engines=[provider])
                self.assertNotIn('class="engine-picker"', form)
                self.assertIn('name="engine"', form)
                self.assertIn('value="' + provider + '"', form)

    def test_choose_any_enabled_engine(self):
        form = _form('Google', visible_engines=['DuckDuckGo', 'Google'])
        self.assertIn('name="engine" value="Google"', form)
        self.assertIn('data-engine="Google"', form)
        self.assertIn('data-engine="DuckDuckGo"', form)
        self.assertNotIn('data-engine="NOMIKO Search"', form)

    def test_home_and_results_work(self):
        h = render_home('#9A82FF', [], engine='DuckDuckGo',
                        visible_engines=['DuckDuckGo', 'Google'])
        self.assertIn('class="engine-picker"', h)
        search = render_search_results('test', '#9A82FF', [], [],
                                       visible_engines=['DuckDuckGo', 'Google'])
        self.assertIn('class="engine-picker"', search)


class BookmarkRailTests(unittest.TestCase):
    def test_rail_only_after_first_bookmark(self):
        self.assertFalse(has_bookmark_toolbar_content([]))
        self.assertTrue(has_bookmark_toolbar_content([{'url':'https://example.com'}]))
        self.assertTrue(has_bookmark_toolbar_content([{'url':'https://example.com','folder':'toolbar'}]))
        self.assertFalse(has_bookmark_toolbar_content([{'url':'https://example.com','folder':'other'}]))
        self.assertFalse(has_bookmark_toolbar_content([{'url':'javascript:alert(1)'}]))

    def test_ui_refresh_and_position_recheck(self):
        code = (ROOT / 'src/ui.py').read_text(encoding='utf-8')
        self.assertIn('self.setVisible(bool(records) and self.browser.store.settings.get', code)
        self.assertIn('has_bookmark_toolbar_content(self.store.bookmarks)', code)

    def test_update_version(self):
        from src.update_trust import CURRENT_VERSION
        self.assertEqual(CURRENT_VERSION, '0.9.10')
        self.assertEqual((ROOT / '.github/release-request.txt').read_text().strip(), 'PUBLISH v0.9.10-alpha')
