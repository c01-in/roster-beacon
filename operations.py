"""One per-user operation lock for the launcher, updater and restore command."""

from i18n import localize
from contextlib import contextmanager
import msvcrt

from app_runtime import load_settings, path_setting


@contextmanager
def operation_lock():
    root = path_setting(load_settings(), 'data_directory')
    root.mkdir(parents=True, exist_ok=True)
    with (root/'launcher.lock').open('a+b') as stream:
        stream.seek(0)
        if not stream.read(1):
            stream.write(b'0')
            stream.flush()
        stream.seek(0)
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            raise RuntimeError(localize('另一个更新、启动或恢复操作正在运行，请稍后再试')) from error
        try:
            yield
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
