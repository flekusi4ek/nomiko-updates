"""Discord invite deep-link regression tests. No web/Discord account needed."""
from pathlib import Path
from unittest import TestCase, mock

from src import discord_links
from src.storage import DEFAULT_SETTINGS
from src.update_trust import CURRENT_VERSION, CURRENT_CHANNEL

ROOT = Path(__file__).resolve().parents[1]


class DiscordInviteTests(TestCase):
    def test_only_actual_invite_hosts_and_paths(self):
        valid = {
            'https://discord.gg/Fn-Es_123?utm_source=foo': 'Fn-Es_123',
            'https://www.discord.gg/XyZ': 'XyZ',
            'https://discord.com/invite/XyZ': 'XyZ',
            'https://www.discord.com/invite/abc123/': 'abc123',
            'https://discordapp.com/invite/abcDEF': 'abcDEF',
            'https://canary.discord.com/invite/Alpha': 'Alpha',
            'https://ptb.discord.com/invite/Alpha': 'Alpha',
        }
        for url, expected in valid.items():
            with self.subTest(url=url):
                self.assertEqual(discord_links.discord_invite_code(url), expected)
        malicious = (
            'https://discord.gg.evil.org/Invite',
            'https://discord.com.attacker.org/invite/abc',
            'https://fake-discord.gg/abc',
            'https://discord.com/oauth2/authorize?client_id=123',
            'https://discord.com/login',
            'https://discord.com/channels/@me',
            'https://discord.gg/',
            'https://discord.gg/code/extra',
            'https://discord.com/invite',
            'https://discord.com/invite/code/extra',
            'https://discord.gg/a%2Fb',
            'https://discord.gg/abc%00',
            'https://discord.gg/a',
            'https://user:pass@discord.gg/abc',
            'https://discord.gg:444/abc',
            'file:///C:/discord.gg/abc',
            'javascript:alert(1)',
        )
        for url in malicious:
            with self.subTest(url=url):
                self.assertIsNone(discord_links.discord_invite_code(url))

    def test_only_real_user_top_level_navigation_can_launch(self):
        value = 'https://discord.gg/fncustoms'
        for navigation in (0, 1):
            self.assertTrue(discord_links.should_open_in_discord(
                value, navigation, main_frame=True, enabled=True))
        for navigation in (2, 3, 4, 5, 6):
            self.assertFalse(discord_links.should_open_in_discord(value, navigation))
        self.assertFalse(discord_links.should_open_in_discord(value, 0, main_frame=False))
        self.assertFalse(discord_links.should_open_in_discord(value, 1, enabled=False))
        self.assertFalse(discord_links.should_open_in_discord(value, 1, restoring_session=True))
        self.assertFalse(discord_links.should_open_in_discord(
            'https://discord.com/oauth2/authorize', 0))

    def test_windows_protocol_invoked_without_sending_credentials(self):
        value = 'https://discord.gg/Fn3-Code?someTracking=1'
        with mock.patch.object(discord_links, 'discord_protocol_registered', return_value=True), \
                mock.patch.object(discord_links.os, 'startfile', create=True) as launch:
            self.assertTrue(discord_links.open_discord_invite(value))
            launch.assert_called_once_with('discord://-/invite/Fn3-Code')
        with mock.patch.object(discord_links, 'discord_protocol_registered', return_value=False), \
                mock.patch.object(discord_links.os, 'startfile', create=True) as launch:
            self.assertFalse(discord_links.open_discord_invite(value))
            launch.assert_not_called()

    def test_failed_launch_preserves_browser_fallback(self):
        with mock.patch.object(discord_links, 'discord_protocol_registered', return_value=True), \
                mock.patch.object(discord_links.os, 'startfile', create=True, side_effect=OSError('No handler')):
            self.assertFalse(discord_links.open_discord_invite('https://discord.gg/test'))

    def test_setting_is_reversible_and_implemented_in_qt_navigation(self):
        ui = (ROOT / 'src/ui.py').read_text(encoding='utf-8')
        settings = (ROOT / 'src/settings_page.py').read_text(encoding='utf-8')
        storage = (ROOT / 'src/storage.py').read_text(encoding='utf-8')
        self.assertTrue(DEFAULT_SETTINGS['discord_invites_in_app'])
        self.assertIn("discord_invites_in_app", storage)
        self.assertIn("Open Discord server invites in the desktop app", settings)
        self.assertIn("self.set_preference(discord_invites_in_app=enabled)", settings)
        self.assertIn("should_open_in_discord(", ui)
        self.assertIn("open_discord_invite(url.toString())", ui)
        self.assertIn("if open_discord_invite(url.toString()):", ui)
        self.assertIn("return False", ui)
        self.assertIn("return super().acceptNavigationRequest(", ui)

    def test_stable_release_marker(self):
        self.assertEqual((CURRENT_VERSION, CURRENT_CHANNEL), ('0.9.17', 'stable'))
        self.assertEqual((ROOT / '.github/release-request.txt').read_text().strip(),
                         'PUBLISH v0.9.17')


if __name__ == '__main__':
    import unittest
    unittest.main()
