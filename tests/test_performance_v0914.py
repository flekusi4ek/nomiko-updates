"""Performance policy regressions for older Windows CPUs."""
from pathlib import Path
from unittest import TestCase
from src.performance import freeze_after_seconds, should_freeze_background
from src.rendering import rendering_mode, chromium_flags
from src.storage import DEFAULT_SETTINGS
from src.update_trust import CURRENT_VERSION, CURRENT_CHANNEL

ROOT = Path(__file__).resolve().parents[1]


class PerformanceRegressionTests(TestCase):
    def test_default_uses_qt_gpu_fallback_not_forced_software(self):
        self.assertEqual(rendering_mode(DEFAULT_SETTINGS), 'hardware')
        self.assertEqual(chromium_flags('hardware'), '')
        self.assertEqual(chromium_flags('compatibility'), '--disable-gpu')
        self.assertEqual(rendering_mode({'graphics_mode': 'invalid'}), 'hardware')

    def test_idle_policy_never_freezes_active_music_pinned_or_loading_tabs(self):
        base = dict(idle_seconds=600, visible=False, loading=False,
                    audible=False, pinned=False, recommended_allows_freeze=True)
        self.assertTrue(should_freeze_background('balanced', **base))
        for key in ('visible', 'loading', 'audible', 'pinned'):
            blocked = dict(base, **{key: True})
            self.assertFalse(should_freeze_background('balanced', **blocked))
        self.assertFalse(should_freeze_background(
            'balanced', **dict(base, recommended_allows_freeze=False)))

    def test_balanced_requires_grace_period_and_off_never_sleeps(self):
        self.assertIsNone(freeze_after_seconds('off'))
        self.assertGreater(freeze_after_seconds('balanced'), 90)
        base = dict(idle_seconds=60, visible=False, loading=False,
                    audible=False, pinned=False, recommended_allows_freeze=True)
        self.assertFalse(should_freeze_background('balanced', **base))
        base['idle_seconds'] = 99999
        self.assertFalse(should_freeze_background('off', **base))

    def test_modes_have_increasing_savings(self):
        self.assertGreater(freeze_after_seconds('balanced'),
                           freeze_after_seconds('gaming'))
        self.assertGreater(freeze_after_seconds('gaming'),
                           freeze_after_seconds('ultra'))

    def test_ui_resumes_on_activation_and_never_discards(self):
        ui = (ROOT / 'src/ui.py').read_text(encoding='utf-8')
        self.assertIn('page.recommendedState() != state.Active', ui)
        self.assertIn('page.recentlyAudible()', ui)
        self.assertIn('page.isLoading()', ui)
        self.assertIn('self._idle_since[previous] = now', ui)
        self.assertIn('page.setLifecycleState(state.Frozen)', ui)
        self.assertIn('page.setLifecycleState(state.Active)', ui)
        maintain = ui[ui.index('def _maintain_background_tabs('):
                      ui.index('def on_widget_action(')]
        self.assertNotIn('state.Discarded', maintain)
        self.assertNotIn('view.reload(', maintain)

    def test_session_saves_are_debounced_and_deduplicated(self):
        ui = (ROOT / 'src/ui.py').read_text(encoding='utf-8')
        store = (ROOT / 'src/storage.py').read_text(encoding='utf-8')
        self.assertIn('self._session_timer.setInterval(2200)', ui)
        self.assertIn("if payload == getattr(self, '_last_saved_session', None)", store)
        self.assertIn("self._last_saved_session = payload", store)
        self.assertIn('self._tab_width_timer.start(16)', ui)

    def test_migration_is_one_time_with_user_override_available(self):
        store = (ROOT / 'src/storage.py').read_text(encoding='utf-8')
        settings = (ROOT / 'src/settings_page.py').read_text(encoding='utf-8')
        self.assertIn("_v0914_graphics_migrated", store)
        self.assertIn("('compatibility', 'Compatibility · software rendering')", settings)
        self.assertIn("('hardware', 'Automatic GPU acceleration · recommended')", settings)

    def test_stable_version_and_no_network_probe_in_ci(self):
        self.assertEqual((CURRENT_VERSION, CURRENT_CHANNEL), ('0.9.16', 'stable'))
        self.assertEqual((ROOT / '.github/release-request.txt').read_text().strip(),
                         'PUBLISH v0.9.16')
        workflow = (ROOT / '.github/workflows/windows.yml').read_text()
        self.assertNotIn('Diagnose real Technical City page', workflow)
        self.assertIn('Smoke-test first-frame rendering and tab switching', workflow)
        self.assertIn('Verify in-app update helper upgrades the original custom folder', workflow)


if __name__ == '__main__':
    import unittest
    unittest.main()
