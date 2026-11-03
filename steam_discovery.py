"""Read Steam installation metadata without changing Steam or account files."""
from __future__ import annotations

import os
from pathlib import Path
import re
import winreg


def steam_roots():
    candidates = []
    for hive, key, name in [(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam', 'SteamPath'),
                             (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Valve\Steam', 'InstallPath')]:
        try:
            with winreg.OpenKey(hive, key) as handle:
                candidates.append(Path(winreg.QueryValueEx(handle, name)[0]))
        except OSError:
            pass
    for env in ('PROGRAMFILES(X86)', 'PROGRAMFILES'):
        if os.environ.get(env):
            candidates.append(Path(os.environ[env])/'Steam')
    return list(dict.fromkeys(p.resolve() for p in candidates if p.is_dir()))


def values(text):
    return {k.lower(): v.replace('\\\\', '\\') for k, v in re.findall(r'"([^"\n]+)"\s*"([^"\n]*)"', text)}


def discover():
    roots = steam_roots()
    libraries = set(roots)
    for root in roots:
        file = root/'steamapps/libraryfolders.vdf'
        if file.is_file():
            for value in re.findall(r'"path"\s*"([^"]+)"', file.read_text('utf-8', errors='replace')):
                libraries.add(Path(value.replace('\\\\', '\\')))
    games = []
    for library in sorted(libraries):
        for file in (library/'steamapps').glob('appmanifest_*.acf'):
            data = values(file.read_text('utf-8', errors='replace'))
            if not re.search(r'NBA\s*2K\d+', data.get('name', ''), re.I):
                continue
            folder = library/'steamapps/common'/data.get('installdir', '')
            exes = [p for p in folder.glob('*.exe') if re.fullmatch(r'NBA\s*2K\d+\.exe', p.name, re.I)]
            if not exes:
                continue
            appid = data.get('appid', '')
            saves = []
            for root in roots:
                for account in (root/'userdata').glob('*'):
                    if not account.is_dir() or not account.name.isdigit():
                        continue
                    app = account/appid
                    for tail in ('local/pls/sync', 'remote/pls/sync', 'remote/sync', 'local/sync'):
                        path = app/tail
                        if path.is_dir() and list(path.glob('manifest_*.bin')):
                            saves.append(dict(account=account.name, path=str(path)))
            games.append(dict(name=data['name'], app_id=appid, executable=str(exes[0]),
                              library=str(library), sync_candidates=saves))
    return games
