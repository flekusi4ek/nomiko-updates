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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--installer', required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--app-dir', required=True)
    args = parser.parse_args()
    if args.pid <= 0 or not installer_is_safe(Path(args.installer), args.sha256):
        record_update_status('Update aborted: installer verification failed.')
        return 3
    if not wait_for_pid(args.pid):
        record_update_status('Update aborted: NOMIKO did not close within the timeout.')
        return 4
    if not wait_for_browser_shutdown(Path(args.app_dir)):
        record_update_status('Update deferred: a NOMIKO or QtWebEngineProcess child is still running.')
        return 6
    # The browser and its child processes have exited; re-check signed payload.
    if not installer_is_safe(Path(args.installer), args.sha256):
        record_update_status('Update aborted: installer checksum mismatch.')
        return 5
    proc = subprocess.run([str(Path(args.installer)), '/S'], timeout=300, check=False)
    record_update_status('Update installed.' if proc.returncode == 0
                         else f'Installer failed with code {proc.returncode}.')
    return proc.returncode


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        sys.exit(10)
