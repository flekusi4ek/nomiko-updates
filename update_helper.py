"""Separate Windows updater process. Waits for NOMIKO to exit before running NSIS."""
from __future__ import annotations

import argparse
import ctypes
import ctypes.wintypes
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import time


def wait_for_pid(pid: int, seconds: int = 120) -> bool:
    if os.name != 'nt':
        return False
    SYNCHRONIZE = 0x00100000
    WAIT_OBJECT_0 = 0
    WAIT_TIMEOUT = 258
    kernel = ctypes.windll.kernel32
    kernel.OpenProcess.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.BOOL, ctypes.wintypes.DWORD]
    kernel.OpenProcess.restype = ctypes.wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD]
    kernel.WaitForSingleObject.restype = ctypes.wintypes.DWORD
    kernel.CloseHandle.argtypes = [ctypes.wintypes.HANDLE]
    handle = kernel.OpenProcess(SYNCHRONIZE, False, pid)
    if not handle:
        return True  # process already exited
    try:
        return kernel.WaitForSingleObject(handle, seconds * 1000) == WAIT_OBJECT_0
    finally:
        kernel.CloseHandle(handle)


def installer_is_safe(path: Path, checksum: str) -> bool:
    if not re.fullmatch('[a-f0-9]{64}', checksum):
        return False
    local = os.environ.get('LOCALAPPDATA') or str(Path.home() / 'AppData' / 'Local')
    allowed = (Path(local) / 'NOMIKO' / 'updates').resolve()
    p = path.resolve()
    if p.parent != allowed or not re.fullmatch(r'NOMIKO-Setup-\d+\.\d+\.\d+(?:-alpha|-beta|-rc)?\.exe', p.name):
        return False
    if not p.is_file():
        return False
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest() == checksum


def running_browser_processes(install_dir: Path) -> list[int]:
    """Return PIDs of browser/Qt helpers loading binaries from this installation."""
    if os.name != 'nt':
        return []
    # Native ToolHelp API: no external PowerShell/psutil dependency.
    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ('dwSize', ctypes.wintypes.DWORD), ('cntUsage', ctypes.wintypes.DWORD),
            ('th32ProcessID', ctypes.wintypes.DWORD), ('th32DefaultHeapID', ctypes.c_void_p),
            ('th32ModuleID', ctypes.wintypes.DWORD), ('cntThreads', ctypes.wintypes.DWORD),
            ('th32ParentProcessID', ctypes.wintypes.DWORD), ('pcPriClassBase', ctypes.c_long),
            ('dwFlags', ctypes.wintypes.DWORD), ('szExeFile', ctypes.c_wchar * 260)
        ]
    kernel = ctypes.windll.kernel32
    kernel.CreateToolhelp32Snapshot.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = ctypes.wintypes.HANDLE
    kernel.Process32FirstW.argtypes = [ctypes.wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
    kernel.Process32FirstW.restype = ctypes.wintypes.BOOL
    kernel.Process32NextW.argtypes = [ctypes.wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
    kernel.Process32NextW.restype = ctypes.wintypes.BOOL
    kernel.OpenProcess.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.BOOL,
                                   ctypes.wintypes.DWORD]
    kernel.OpenProcess.restype = ctypes.wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [
        ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD, ctypes.c_wchar_p,
        ctypes.POINTER(ctypes.wintypes.DWORD)]
    kernel.QueryFullProcessImageNameW.restype = ctypes.wintypes.BOOL
    kernel.CloseHandle.argtypes = [ctypes.wintypes.HANDLE]
    kernel.CloseHandle.restype = ctypes.wintypes.BOOL
    snapshot = kernel.CreateToolhelp32Snapshot(0x00000002, 0)
    if not snapshot or snapshot == ctypes.c_void_p(-1).value:
        return []
    root = os.path.normcase(os.path.normpath(str(install_dir.resolve()))) + os.sep
    busy = []
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        more = kernel.Process32FirstW(snapshot, ctypes.byref(entry))
        while more:
            if entry.szExeFile.lower() in ('nomiko.exe', 'qtwebengineprocess.exe'):
                proc = kernel.OpenProcess(0x1000, False, entry.th32ProcessID)
                if proc:
                    try:
                        buf = ctypes.create_unicode_buffer(32768)
                        length = ctypes.wintypes.DWORD(len(buf))
                        if kernel.QueryFullProcessImageNameW(proc, 0, buf, ctypes.byref(length)):
                            candidate = os.path.normcase(os.path.normpath(buf.value))
                            if candidate.startswith(root):
                                busy.append(int(entry.th32ProcessID))
                    finally:
                        kernel.CloseHandle(proc)
            more = kernel.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel.CloseHandle(snapshot)
    return busy


def wait_for_browser_shutdown(install_dir: Path, seconds: int = 90) -> bool:
    """Wait for child renderer processes to release all in-place Qt binaries."""
    deadline = time.monotonic() + seconds
    while True:
        if not running_browser_processes(install_dir):
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.5)


def record_update_status(message: str) -> None:
    """Leave a brief failure reason when the background helper cannot show UI."""
    try:
        local = os.environ.get('LOCALAPPDATA') or str(Path.home() / 'AppData' / 'Local')
        folder = Path(local) / 'NOMIKO' / 'updates'
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'last-update-status.txt').write_text(message + '\n', encoding='utf-8')
    except OSError:
        pass


def installer_command(installer: Path, install_dir: Path, silent: bool = False) -> str:
    """Build the exact NSIS Windows command line.

    NSIS requires /D=<existing folder> as the LAST parameter, literally
    without quotation marks, even when the folder contains spaces.
    Python's ordinary list2cmdline would quote the parameter and break /D.
    """
    folder = str(install_dir)
    if not folder or any(c in folder for c in ('"', '\r', '\n')):
        raise ValueError('Invalid installed browser folder')
    prefix = subprocess.list2cmdline([str(installer)] + (['/S'] if silent else []))
    return prefix + ' /D=' + folder


def notify_failure(message: str, silent: bool = False) -> None:
    record_update_status(message)
    if silent or os.name != 'nt':
        return
    try:
        ctypes.windll.user32.MessageBoxW(
            None, message + '\n\nIf needed, install NOMIKO manually from GitHub Releases.',
            'NOMIKO update failed', 0x10)
    except (OSError, AttributeError):
        pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--installer', required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--app-dir', required=True)
    parser.add_argument('--ready-file', default='')
    parser.add_argument('--silent', action='store_true', help='CI-only silent installer')
    args = parser.parse_args()
    installer = Path(args.installer).resolve()
    app_dir = Path(args.app_dir).resolve()
    if args.pid <= 0 or not installer_is_safe(installer, args.sha256):
        notify_failure('Update aborted: installer verification failed.', args.silent)
        return 3
    if not app_dir.is_dir() or not (app_dir / 'NOMIKO.exe').is_file():
        notify_failure('Update aborted: could not locate the installed NOMIKO.exe.', args.silent)
        return 7
    # Signal that the independent helper is READY before the browser shuts down.
    # The browser must not exit on a failed or blocked helper launch.
    if args.ready_file:
        ready = Path(args.ready_file).resolve()
        cache = installer.parent
        if ready.parent != cache:
            notify_failure('Update aborted: invalid readiness marker.', args.silent)
            return 8
        ready.write_text('NOMIKO helper ready', encoding='utf-8')
    record_update_status('Installer verified; waiting for NOMIKO to close.')
    if not wait_for_pid(args.pid):
        notify_failure('Update aborted: NOMIKO did not close. Close all NOMIKO windows.', args.silent)
        return 4
    if not wait_for_browser_shutdown(app_dir):
        notify_failure('Update deferred: NOMIKO or QtWebEngineProcess is still running. Restart Windows and use the downloaded installer.', args.silent)
        return 6
    if not installer_is_safe(installer, args.sha256):
        notify_failure('Update aborted: installer checksum mismatch.', args.silent)
        return 5
    record_update_status('NOMIKO closed; starting installer in the original installation folder.')
    # Visible by default: display actual NSIS errors instead of silently
    # swallowing them. /D preserves custom install paths and pinned shortcuts.
    command = installer_command(installer, app_dir, args.silent)
    proc = subprocess.run(command, timeout=600, check=False)
    if proc.returncode == 0 and (app_dir / 'NOMIKO.exe').is_file():
        record_update_status('Update installed.')
    else:
        notify_failure(f'Installer failed with code {proc.returncode}. Installation folder: {app_dir}', args.silent)
    return proc.returncode


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:
        import traceback
        record_update_status('Updater error: ' + str(exc) + '\n' + traceback.format_exc())
        notify_failure('NOMIKO updater encountered an error: ' + str(exc))
        sys.exit(10)
