"""Platform compatibility layer — subprocess window suppression on Windows."""
import sys
import subprocess

_original_run = subprocess.run
_original_check_output = subprocess.check_output


def _patched_run(*args, **kwargs):
    if sys.platform == 'win32' and 'creationflags' not in kwargs:
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW  # CREATE_NO_WINDOW
    return _original_run(*args, **kwargs)


def _patched_check_output(*args, **kwargs):
    if sys.platform == 'win32' and 'creationflags' not in kwargs:
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW  # CREATE_NO_WINDOW
    return _original_check_output(*args, **kwargs)


_patched = False


def patch_subprocess_no_window():
    """全局调用一次：抑制 Windows 下子进程的控制台窗口弹窗。幂等调用。"""
    global _patched
    if _patched:
        return
    subprocess.run = _patched_run
    subprocess.check_output = _patched_check_output
    _patched = True
