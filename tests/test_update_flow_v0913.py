"""Checks for the repaired one-click updater and actual installation folder."""
from pathlib import Path
import unittest
import update_helper

ROOT = Path(__file__).resolve().parents[1]


class UpdateFlowTests(unittest.TestCase):
    def test_nsis_custom_directory_is_last_and_unquoted(self):
        cmd = update_helper.installer_command(
            Path(r'C:\Users\Example User\Downloads\NOMIKO-Setup-0.9.17.exe'),
            Path(r'C:\Users\Example User\Apps\NOMIKO Custom Folder'), True)
        self.assertIn('/S /D=', cmd)
        self.assertTrue(cmd.endswith(r'/D=C:\Users\Example User\Apps\NOMIKO Custom Folder'))
        self.assertNotIn('/D="', cmd)

    def test_interactive_installer_is_visible(self):
        cmd = update_helper.installer_command(
            Path(r'C:\Apps\NOMIKO-Setup-0.9.17.exe'),
            Path(r'C:\Custom NOMIKO'), False)
        self.assertNotIn('/S', cmd)
        self.assertTrue(cmd.endswith(r'/D=C:\Custom NOMIKO'))

    def test_helper_waits_for_shut_down_and_retains_original_folder(self):
        helper = (ROOT / 'update_helper.py').read_text(encoding='utf-8')
        self.assertIn("parser.add_argument('--ready-file'", helper)
        self.assertIn('wait_for_pid(args.pid)', helper)
        self.assertIn('wait_for_browser_shutdown(app_dir)', helper)
        self.assertIn('installer_command(installer, app_dir, silent_installer)', helper)
        self.assertIn('notify_failure(', helper)

    def test_ui_starts_helper_before_closing(self):
        ui = (ROOT / 'src/ui.py').read_text(encoding='utf-8')
        update_ui = (ROOT / 'src/update_ui.py').read_text(encoding='utf-8')
        self.assertIn('def launch_verified_update(self, installer, release):', ui)
        self.assertIn('shutil.copy2(helper, staged_helper)', ui)
        self.assertIn('if ready.is_file():', ui)
        self.assertIn('QApplication.instance().closeAllWindows()', ui)
        self.assertIn('self.browser.launch_verified_update(self.installer, self.release)', update_ui)
        self.assertNotIn('self.browser._pending_update =', update_ui)

    def test_windows_ci_includes_real_helper_update(self):
        workflow = (ROOT / '.github/workflows/windows.yml').read_text(encoding='utf-8')
        self.assertIn('Verify in-app update helper upgrades the original custom folder', workflow)
        self.assertIn('NOMIKO Custom Folder', workflow)
        self.assertIn(" '--silent')", workflow)

    def test_stable_version(self):
        from src.update_trust import CURRENT_VERSION, CURRENT_CHANNEL
        self.assertEqual((CURRENT_VERSION, CURRENT_CHANNEL), ('0.9.17', 'stable'))


if __name__ == '__main__':
    unittest.main()
