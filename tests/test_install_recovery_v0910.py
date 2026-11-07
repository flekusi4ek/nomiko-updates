"""Release and regression checks for safe Windows recovery upgrades."""
from pathlib import Path
from unittest import TestCase, mock
import update_helper

ROOT = Path(__file__).resolve().parents[1]


class InstallerRecoveryTests(TestCase):
    def test_installer_stages_before_swapping(self):
        nsi = (ROOT / 'installer/NOMIKO.nsi').read_text(encoding='utf-8')
        self.assertIn('SetOutPath "$R8"', nsi)
        self.assertIn('Rename "$INSTDIR" "$R9"', nsi)
        self.assertIn('Rename "$R8" "$INSTDIR"', nsi)
        self.assertIn('Rename "$R9" "$INSTDIR"', nsi)
        self.assertLess(nsi.index('File /r "..\\dist\\NOMIKO\\*"'),
                        nsi.index('Rename "$INSTDIR" "$R9"'))
        self.assertIn('IfErrors install_locked', nsi)
        self.assertIn('SetErrorLevel 2', nsi)

    def test_main_self_check_smoke(self):
        main = (ROOT / 'main.py').read_text(encoding='utf-8')
        workflow = (ROOT / '.github/workflows/windows.yml').read_text()
        self.assertIn("if '--self-check' in sys.argv:", main)
        self.assertIn('Smoke-test packaged Qt WebEngine imports', workflow)
        self.assertIn('Smoke-test installed NOMIKO', workflow)

    def test_helper_waits_on_renderer(self):
        helper = (ROOT / 'update_helper.py').read_text()
        ui = (ROOT / 'src/ui.py').read_text()
        self.assertIn("'qtwebengineprocess.exe'", helper)
        self.assertIn('wait_for_browser_shutdown(app_dir)', helper)
        self.assertIn("'--app-dir', str(Path(sys.executable).resolve().parent)", ui)

    def test_shutdown_wait_is_bounded_and_checks_again(self):
        with mock.patch.object(update_helper, 'running_browser_processes',
                               side_effect=[[123], [], []]) as running, \
             mock.patch.object(update_helper.time, 'sleep'):
            self.assertTrue(update_helper.wait_for_browser_shutdown(Path('C:/NOMIKO'), 2))
            self.assertEqual(running.call_count, 2)

    def test_version(self):
        from src.update_trust import CURRENT_VERSION
        self.assertEqual(CURRENT_VERSION, '0.9.15')
        self.assertEqual((ROOT / '.github/release-request.txt').read_text().strip(),
                         'PUBLISH v0.9.15')
