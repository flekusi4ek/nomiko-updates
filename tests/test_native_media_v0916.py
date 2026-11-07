"""Qt-native media fallback checks: source safety and user-triggered integration."""
from pathlib import Path
from unittest import TestCase

from src.native_media import (safe_remote_url, soundcloud_track_url,
                              normalize_media_source, select_audio_url)

ROOT = Path(__file__).resolve().parents[1]


class NativeMediaTests(TestCase):
    def test_remote_sources_are_https_only_and_public(self):
        self.assertTrue(safe_remote_url('https://fnggcdn.com/items/123/video.mp4'))
        self.assertTrue(safe_remote_url('https://cf-media.sndcdn.com/a.mp3?token=abc'))
        for x in ('http://example.org/a.mp4', 'file:///C:/secret.txt',
                  'https://localhost:443/private', 'https://127.0.0.1/media',
                  'https://10.1.2.3/media', 'https://[::1]/audio',
                  'https://user:pass@example.org/audio', 'data:audio/wav;base64,',
                  'javascript:alert(1)', 'https://localhost.example.local/audio'):
            self.assertFalse(safe_remote_url(x), x)

    def test_soundcloud_only_real_public_track_links(self):
        for url in ('https://soundcloud.com/artist-a/a-song',
                    'https://www.soundcloud.com/artist-b/track'):
            self.assertTrue(soundcloud_track_url(url), url)
        for url in ('https://soundcloud.com/you/likes',
                    'https://soundcloud.com/artist/sets',
                    'https://soundcloud.com/artist/sets/playlist',
                    'https://fake-soundcloud.com/artist/song',
                    'https://soundcloud.com.evil.org/artist/song'):
            self.assertFalse(soundcloud_track_url(url), url)

    def test_extractor_results_without_download_or_account_data(self):
        self.assertEqual(select_audio_url({'url':'https://example.org/track.mp3'}),
                         'https://example.org/track.mp3')
        self.assertEqual(select_audio_url({'formats':[
            {'url':'https://example.org/v.mp4','acodec':'none'},
            {'url':'https://example.org/a.m3u8','acodec':'opus'}
        ]}), 'https://example.org/a.m3u8')
        self.assertEqual(select_audio_url({'url':'file:///etc/passwd'}), '')
        self.assertFalse(normalize_media_source('https://soundcloud.com/you/likes',
                                                'soundcloud'))
        self.assertTrue(normalize_media_source(
            'https://fnggcdn.com/items/123/video.mp4', 'direct'))

    def test_native_web_engine_bridge_is_click_activated(self):
        js = (ROOT / 'src/media_bridge.py').read_text(encoding='utf-8')
        ui = (ROOT / 'src/ui.py').read_text(encoding='utf-8')
        self.assertIn('install_media_script(self.profile)', ui)
        self.assertIn('def open_native_media(self, source, kind=', ui)
        self.assertIn("url.path() == '/media'", ui)
        self.assertIn('normalize_media_source(media_url, kind)', ui)
        self.assertIn('Play with NOMIKO Media Player', ui)
        self.assertIn("location.hostname === 'fortnite.gg'", js)
        self.assertIn("document.addEventListener('error'", js)
        self.assertIn("new MutationObserver(schedule)", js)
        self.assertIn('soundList__item', js)
        self.assertIn('▶ Play in NOMIKO', js)
        self.assertNotIn('WebView2', js)
        self.assertNotIn('navigator.mediaDevices.getUserMedia(', js)

    def test_local_ffmpeg_backend_is_explicit_in_smoke(self):
        smoke = (ROOT / 'tools/native_media_smoke.py').read_text(encoding='utf-8')
        requirements = (ROOT / 'requirements.txt').read_text(encoding='utf-8')
        wf = (ROOT / '.github/workflows/windows.yml').read_text(encoding='utf-8')
        self.assertIn("'QT_MEDIA_BACKEND'] = 'ffmpeg'", smoke)
        self.assertIn('QMediaPlayer', smoke)
        self.assertIn('yt-dlp', requirements)
        self.assertIn('Smoke-test Qt Multimedia FFmpeg backend', wf)
        self.assertIn('--collect-all PySide6.QtMultimedia', wf)
        self.assertIn('--collect-all yt_dlp', wf)

    def test_release(self):
        from src.update_trust import CURRENT_VERSION, CURRENT_CHANNEL
        self.assertEqual((CURRENT_VERSION, CURRENT_CHANNEL), ('0.9.17','stable'))
