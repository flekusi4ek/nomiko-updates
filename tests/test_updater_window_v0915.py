"""Regression tests for the standalone NOMIKO 0.9.16 update window."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase, mock
import tempfile

import update_helper

ROOT = Path(__file__).resolve().parents[1]


class StandaloneUpdateTests(TestCase):
    def test_ui_and_helper_are_independent_from_qt_webengine(self):
        code = (ROOT / 'updater_window.py').read_text(encoding='utf-8')
        helper = (ROOT / 'update_helper.py').read_text(encoding='utf-8')
        self.assertIn('class UpdateWindow:', code)
        self.assertIn("text='NOMIKO'", code)
        self.assertIn("text='Open NOMIKO'", code)
        self.assertIn('self.progress', code)
        self.assertIn("self.root.protocol('WM_DELETE_WINDOW', self._on_close)", code)
        self.assertIn("def run_update_window(worker, *, app_dir, installer):", code)
        self.assertNotIn('PySide6', code)
        self.assertIn("if '--ui-self-check' in sys.argv:", helper)

    def test_window_is_started_only_after_browser_exits(self):
        source = (ROOT / 'update_helper.py').read_text(encoding='utf-8')
        main = source[source.index('def main() -> int:'):]
        self.assertLess(main.index('ready.write_text('), main.index('wait_for_pid(args.pid)'))
        self.assertLess(main.index('wait_for_pid(args.pid)'), main.index('run_update_window('))
        self.assertIn('if args.silent:', main)
        self.assertIn('silent_installer=True, progress=progress', main)
        self.assertIn('except (ImportError, tkinter.TclError)', main)

    def test_visual_install_is_silent_nsis_with_real_stage_updates(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = Path(tmp) / 'NOMIKO Custom Folder'
            app.mkdir()
            (app / 'NOMIKO.exe').touch()
            installer = Path(tmp) / 'NOMIKO-Setup-0.9.16.exe'
            statuses = []
            args = SimpleNamespace(sha256='a' * 64)
            with mock.patch.object(update_helper, 'wait_for_browser_shutdown', return_value=True), \
                 mock.patch.object(update_helper, 'installer_is_safe', return_value=True), \
                 mock.patch.object(update_helper, 'record_update_status'), \
                 mock.patch.object(update_helper.subprocess, 'run', return_value=SimpleNamespace(returncode=0)) as run:
                code = update_helper.perform_install(
                    args, installer, app, silent_installer=True,
                    progress=lambda stage, message: statuses.append((stage, message)))
            self.assertEqual(code, 0)
            self.assertEqual([stage for stage, _ in statuses],
                             ['closing', 'verifying', 'installing', 'complete'])
            command = run.call_args.args[0]
            self.assertIn(' /S /D=', command)
            self.assertTrue(command.endswith(str(app)))
            self.assertEqual(run.call_args.kwargs['timeout'], 600)

    def test_failure_is_visible_and_does_not_start_installer(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = Path(tmp)
            statuses = []
            with mock.patch.object(update_helper, 'wait_for_browser_shutdown', return_value=False), \
                 mock.patch.object(update_helper, 'record_update_status'), \
                 mock.patch.object(update_helper.subprocess, 'run') as run:
                code = update_helper.perform_install(
                    SimpleNamespace(sha256='b' * 64), app / 'NOMIKO-Setup-0.9.16.exe',
                    app, silent_installer=True,
                    progress=lambda stage, message: statuses.append((stage, message)))
            self.assertEqual(code, 6)
            self.assertEqual([v[0] for v in statuses], ['closing', 'error'])
            run.assert_not_called()

    def test_ci_builds_and_smokes_packaged_tk_window(self):
        workflow = (ROOT / '.github/workflows/windows.yml').read_text(encoding='utf-8')
        self.assertIn('--onefile --windowed --name NOMIKO-UpdateHelper', workflow)
        self.assertIn("Smoke-test independent updater progress window", workflow)
        self.assertIn("-ArgumentList '--ui-self-check'", workflow)
        self.assertIn("Verify in-app update helper upgrades the original custom folder",
                      workflow)

    def test_version_is_stable(self):
        from src.update_trust import CURRENT_VERSION, CURRENT_CHANNEL
        self.assertEqual(CURRENT_VERSION, '0.9.16')
        self.assertEqual(CURRENT_CHANNEL, 'stable')
        self.assertEqual((ROOT / '.github/release-request.txt').read_text().strip(),
                         'PUBLISH v0.9.16')
