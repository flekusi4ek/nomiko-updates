"""NOMIKO 0.9.4 zoom and tab-preservation regression tests (offline)."""
import unittest
from pathlib import Path

from src.zoom_settings import ZOOM_LEVELS, zoom_percent, zoom_text_only
from src.zoom import text_zoom_javascript, configure_zoom_script, SCRIPT_NAME

ROOT = Path(__file__).resolve().parents[1]


class ZoomSettingsTests(unittest.TestCase):
    def test_default_zoom_is_100(self):
        self.assertEqual(zoom_percent({}), 100)
        self.assertFalse(zoom_text_only({}))

    def test_supported_zoom_levels(self):
        self.assertIn(100, ZOOM_LEVELS)
        for level in (50, 75, 90, 110, 125, 150, 200, 300):
            with self.subTest(level=level):
                self.assertEqual(zoom_percent({'default_zoom': level}), level)

    def test_invalid_zoom_is_rejected(self):
        for value in (0, 5, 500, None, 'abc', {}, []):
            with self.subTest(value=value):
                self.assertEqual(zoom_percent({'default_zoom': value}), 100)

    def test_text_only_requires_true(self):
        self.assertTrue(zoom_text_only({'zoom_text_only': True}))
        for value in (False, None, 'true', 1):
            self.assertFalse(zoom_text_only({'zoom_text_only': value}))

    def test_qt_profile_script_collection_api(self):
        class Collection:
            def __init__(self):
                self.items = []
            def find(self, name):
                return [s for s in self.items if s.name() == name]
            def remove(self, script):
                self.items.remove(script)
            def insert(self, script):
                self.items.append(script)
        class Profile:
            def __init__(self):
                self.collection = Collection()
            def scripts(self):
                return self.collection
        profile = Profile()
        configure_zoom_script(profile, {'default_zoom': 150, 'zoom_text_only': True})
        self.assertEqual(len(profile.collection.items), 1)
        self.assertEqual(profile.collection.items[0].name(), SCRIPT_NAME)
        configure_zoom_script(profile, {'default_zoom': 125, 'zoom_text_only': True})
        self.assertEqual(len(profile.collection.items), 1)
        configure_zoom_script(profile, {'default_zoom': 100, 'zoom_text_only': False})
        self.assertEqual(len(profile.collection.items), 0)

    def test_text_zoom_is_reversible(self):
        active = text_zoom_javascript(150, True)
        inactive = text_zoom_javascript(150, False)
        self.assertIn('const percent = 150, enabled = true', active)
        self.assertIn('const percent = 150, enabled = false', inactive)
        self.assertIn('style.removeProperty("font-size")', active)
        self.assertIn('MutationObserver', active)
        self.assertIn('state.observer.disconnect()', active)
        self.assertIn('location.protocol', active)


class BrowserWiringTests(unittest.TestCase):
    def test_global_and_split_panes(self):
        ui = (ROOT / 'src/ui.py').read_text(encoding='utf-8')
        split = (ROOT / 'src/advanced_ui.py').read_text(encoding='utf-8')
        self.assertIn('configure_zoom_script(self.profile, self.store.settings)', ui)
        self.assertIn('apply_zoom_to_view(self, browser.store.settings)', ui)
        self.assertIn("changed & {'default_zoom', 'zoom_text_only'}", ui)
        self.assertIn('apply_zoom_to_view(tab.left, win.store.settings)', ui)
        self.assertIn('apply_zoom_to_view(tab.right, win.store.settings)', ui)
        self.assertIn('apply_zoom_to_view(self.view, self.browser.store.settings)', split)

    def test_no_background_freeze_or_discard(self):
        ui = (ROOT / 'src/ui.py').read_text(encoding='utf-8')
        handler = ui.split('    def _maintain_background_tabs(self):', 1)[1].split('    def on_widget_action(', 1)[0]
        self.assertNotIn('.setLifecycleState(', handler)
        self.assertNotIn('recommendedState()', handler)
        self.assertNotIn('discard_after', handler)

    def test_settings_controls_and_release(self):
        settings = (ROOT / 'src/settings_page.py').read_text(encoding='utf-8')
        self.assertIn("'Default zoom'", settings)
        self.assertIn("'Zoom text only'", settings)
        from src.update_trust import CURRENT_VERSION
        self.assertEqual(CURRENT_VERSION, '0.9.4')
        self.assertEqual((ROOT / '.github/release-request.txt').read_text().strip(),
                         'PUBLISH v0.9.4-alpha')
