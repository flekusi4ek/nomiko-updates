"""Stable channel, compatibility graphics and tab-paint regressions."""
import unittest
from pathlib import Path

from src.rendering import chromium_flags, configure_webengine, rendering_mode
from src.update_trust import CURRENT_CHANNEL, CURRENT_VERSION
from src.storage import DEFAULT_SETTINGS

ROOT = Path(__file__).resolve().parents[1]


class StableGraphicsTests(unittest.TestCase):
    def test_acceleration_is_default_and_software_is_reversible(self):
        self.assertEqual(DEFAULT_SETTINGS['graphics_mode'], 'hardware')
        self.assertEqual(rendering_mode(DEFAULT_SETTINGS), 'hardware')
        self.assertEqual(chromium_flags('hardware', ''), '')
        self.assertEqual(chromium_flags('compatibility', ''), '--disable-gpu')

    def test_user_can_opt_for_acceleration(self):
        self.assertEqual(chromium_flags('hardware', ''), '')
        self.assertEqual(chromium_flags('hardware', '--foo'), '--foo')

    def test_do_not_duplicate_or_override_existing_chromium_flags(self):
        self.assertEqual(chromium_flags('compatibility', '--foo --disable-gpu'),
                         '--foo --disable-gpu')
        environ = {'QTWEBENGINE_CHROMIUM_FLAGS': '--foo'}
        configure_webengine({'graphics_mode': 'compatibility'}, environ)
        self.assertEqual(environ['QTWEBENGINE_CHROMIUM_FLAGS'], '--foo --disable-gpu')

    def test_only_current_visible_tab_repaints(self):
        ui = (ROOT / 'src/ui.py').read_text(encoding='utf-8')
        self.assertIn('def _refresh_visible_webview(self, view, focus=False)', ui)
        self.assertIn('if not view.isVisible():', ui)
        self.assertIn('view.setFocus(Qt.FocusReason.OtherFocusReason)', ui)
        self.assertIn('QTimer.singleShot(90, lambda v=view:', ui)
        self.assertIn('renderProcessTerminated.connect(', ui)
        self.assertIn('def on_renderer_terminated(self, view, status, exit_code):', ui)
        self.assertNotIn('setLifecycleState(QWebEnginePage.LifecycleState.Discarded)', ui)

    def test_stable_release_is_not_prerelease(self):
        self.assertEqual(CURRENT_VERSION, '0.9.17')
        self.assertEqual(CURRENT_CHANNEL, 'stable')
        self.assertEqual(DEFAULT_SETTINGS['updates_channel'], 'stable')
        self.assertEqual((ROOT / '.github/release-request.txt').read_text().strip(),
                         'PUBLISH v0.9.17')
        workflow = (ROOT / '.github/workflows/windows.yml').read_text()
        self.assertIn('python tools/gui_smoke.py', workflow)
        self.assertIn('--channel stable --installer', workflow)
        self.assertIn('gh release create $tag', workflow)
        self.assertNotIn('--prerelease', workflow)

    def test_installer_stable_version(self):
        nsi = (ROOT / 'installer/NOMIKO.nsi').read_text()
        self.assertIn('NOMIKO-Setup-0.9.17.exe', nsi)
        self.assertIn('Name "${APPNAME} ${VERSION} Stable"', nsi)
        self.assertNotIn('0.9.17-alpha', nsi)

    def test_signed_manifest_rejects_mismatched_stable_identity(self):
        updater = (ROOT / 'src/updater.py').read_text()
        self.assertIn("expected_release_tag = 'v' + version", updater)
        self.assertIn('asset != expected_asset', updater)


if __name__ == '__main__':
    unittest.main()
