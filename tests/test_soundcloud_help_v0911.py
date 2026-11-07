"""Regression tests for the private, opt-in SoundCloud help feature."""
from pathlib import Path
import unittest
from src.blocklists import blocked_by
from src.media_compat import is_soundcloud_host

ROOT = Path(__file__).resolve().parents[1]


class SoundCloudHelpTests(unittest.TestCase):
    def test_exception_does_not_unblock_other_sites(self):
        self.assertEqual(blocked_by('doubleclick.net', 'soundcloud.com'), 'ads')
        self.assertIsNone(blocked_by('doubleclick.net', 'soundcloud.com',
                                     exclusions=('soundcloud.com',)))
        self.assertEqual(blocked_by('doubleclick.net', 'example.org',
                                    exclusions=('soundcloud.com',)), 'ads')

    def test_host_must_be_authentic(self):
        self.assertTrue(is_soundcloud_host('www.soundcloud.com'))
        self.assertFalse(is_soundcloud_host('soundcloud.com.attacker.example'))

    def test_browser_integration(self):
        ui = (ROOT / 'src/ui.py').read_text(encoding='utf-8')
        privacy = (ROOT / 'src/privacy.py').read_text(encoding='utf-8')
        source = (ROOT / 'src/soundcloud_help.py').read_text(encoding='utf-8')
        self.assertIn("menu.addAction('SoundCloud · Playback help…'", ui)
        self.assertIn('def show_soundcloud_playback_help(self):', ui)
        self.assertIn('self.browser.update_preference(block_exceptions=exceptions)', source)
        self.assertIn('self.browser.interceptor.soundcloud_block_count()', source)
        self.assertIn('self._soundcloud_blocked += 1', privacy)
        self.assertNotIn('deleteAllCookies', source)

    def test_current_version(self):
        from src.update_trust import CURRENT_VERSION
        self.assertEqual(CURRENT_VERSION, '0.9.17')


if __name__ == '__main__':
    unittest.main()
