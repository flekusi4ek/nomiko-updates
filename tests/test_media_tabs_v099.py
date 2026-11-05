"""Offline checks for responsive tabs and narrowly scoped SoundCloud playback."""
from pathlib import Path
import unittest
from src.media_compat import is_soundcloud_host, playback_requires_gesture, missing_soundcloud_codecs
from src.tab_layout import fitted_tab_width

ROOT = Path(__file__).resolve().parents[1]


class MediaCompatibilityTests(unittest.TestCase):
    def test_soundcloud_domain_must_be_exact_or_subdomain(self):
        for host in ('soundcloud.com', 'www.soundcloud.com', 'w.soundcloud.com', 'CF.SOUNDCLOUD.COM.'):
            self.assertTrue(is_soundcloud_host(host))
        for host in ('fake-soundcloud.com', 'soundcloud.com.evil.test', '', 'soundcloud.net'):
            self.assertFalse(is_soundcloud_host(host))

    def test_autoplay_guard_is_only_bypassed_on_soundcloud(self):
        self.assertFalse(playback_requires_gesture(True, 'https', 'soundcloud.com'))
        self.assertFalse(playback_requires_gesture(True, 'https', 'w.soundcloud.com'))
        self.assertTrue(playback_requires_gesture(True, 'https', 'example.com'))
        self.assertTrue(playback_requires_gesture(True, 'file', 'soundcloud.com'))
        self.assertFalse(playback_requires_gesture(False, 'https', 'example.com'))

    def test_codec_test_does_not_report_probe_failure_as_missing_codec(self):
        self.assertTrue(missing_soundcloud_codecs({'mp3': False, 'aac': '', 'mse_aac': False}))
        self.assertFalse(missing_soundcloud_codecs({'mp3': 'probably'}))
        self.assertFalse(missing_soundcloud_codecs({'mse_aac': True}))
        self.assertFalse(missing_soundcloud_codecs(None))

    def test_browser_connection(self):
        ui = (ROOT / 'src/ui.py').read_text(encoding='utf-8')
        self.assertIn('self.urlChanged.connect(self.apply_media_policy)', ui)
        self.assertIn('view.apply_media_policy()', ui)
        self.assertIn('missing_soundcloud_codecs(result)', ui)
        self.assertIn('window.MediaSource.isTypeSupported(aac)', ui)


class TabWidthTests(unittest.TestCase):
    def test_equal_widths_and_minimum_for_many_tabs(self):
        for count, expected in ((2, 190), (5, 190), (10, 95), (12, 79), (20, 76)):
            self.assertEqual(fitted_tab_width(950, count), expected)
        self.assertEqual(fitted_tab_width(0, 10), 76)
        self.assertEqual(fitted_tab_width(100, 0), 190)

    def test_responds_to_window_resize_and_keeps_sidebar_layout(self):
        ui = (ROOT / 'src/ui.py').read_text(encoding='utf-8')
        self.assertIn('width = fitted_tab_width(available, count)', ui)
        self.assertIn('self.bar.setUsesScrollButtons(count * width > available)', ui)
        self.assertIn('self.bar.setElideMode(Qt.TextElideMode.ElideRight)', ui)
        self.assertIn("if self.side:\n            # RoundedWest/East", ui)
        self.assertIn('self.bar.setTabToolTip(idx, title)', ui)


if __name__ == '__main__':
    unittest.main()
