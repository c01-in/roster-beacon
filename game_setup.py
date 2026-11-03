"""Discover and validate existing NBA 2K27 local rosters; never create a SYNC."""
import hashlib
import os
from pathlib import Path
import re
import struct
import winreg
import zipfile
import zlib

from app_runtime import load_profile, recommended_data_dir
from baseline_tools import available_manifests, inspect_native_roster
from i18n import tr
from steam_discovery import discover, steam_roots

TAILS = ('local/pls/sync', 'remote/pls/sync', 'remote/sync', 'local/sync', 'pls/sync', 'sync')


def same_path(a, b):
    return bool(a and b) and str(Path(a).resolve()).casefold() == str(Path(b).resolve()).casefold()


def supported_game(path):
    return re.fullmatch(r'NBA\s*2K27\.exe', Path(path).name, re.I) is not None


def installed_games():
    return [g for g in discover() if supported_game(g['executable'])]


def local_app_id(folder):
    for name in ('steam_appid.txt', 'steam_emu.ini', 'steam_api.ini', 'steam_api64.ini'):
        file = folder/name
        if not file.is_file() or file.stat().st_size > 256*1024:
            continue
        text = file.read_text('utf-8-sig', errors='replace')
        value = text.strip() if name == 'steam_appid.txt' else None
        if value and value.isdecimal():
            return value
        match = re.search(r'^\s*(?:AppId|SteamAppId)\s*=\s*(\d+)\s*(?:[#;].*)?$', text, re.I | re.M)
        if match:
            return match[1]
    return ''


def active_steam_user():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam\ActiveProcess') as key:
            account = int(winreg.QueryValueEx(key, 'ActiveUser')[0])
            return str(account) if account else ''
    except (OSError, ValueError, TypeError):
        return ''


def documents_folders():
    paths = [Path.home()/'Documents']
    if os.environ.get('PUBLIC'):
        paths.append(Path(os.environ['PUBLIC'])/'Documents')
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders') as key:
            paths.append(Path(os.path.expandvars(winreg.QueryValueEx(key, 'Personal')[0])))
    except OSError:
        pass
    return list(dict.fromkeys(p.resolve() for p in paths if p.is_dir()))


def discover_game(executable, settings):
    game = Path(executable).expanduser().resolve()
    if not game.is_file() or not supported_game(game):
        raise ValueError(tr('请选择 NBA 2K27 的游戏程序 NBA2K27.exe。'))
    load_profile(settings)
    steam = next((g for g in installed_games() if same_path(g['executable'], game)), None)
    app_id = steam['app_id'] if steam else local_app_id(game.parent)
    folders = {}
    def add(folder, account='', origin='local'):
        folder = Path(folder)
        if folder.is_dir():
            folders.setdefault(str(folder.resolve()).casefold(), dict(path=str(folder.resolve()), account=account, origin=origin))
    if same_path(settings.get('game_executable'), game) and settings.get('sync_directory'):
        add(settings['sync_directory'], origin='configured')
    if app_id:
        for root in steam_roots():
            for account in (root/'userdata').glob('*'):
                if account.is_dir() and account.name.isdecimal():
                    for tail in TAILS:
                        add(account/app_id/tail, account.name, 'steam')
    for document in documents_folders():
        # Bounded provider/application folders, not a recursive disk search.
        steam_saves = document/'Steam'
        if steam_saves.is_dir():
            for provider in steam_saves.iterdir():
                if not provider.is_dir():
                    continue
                apps = [provider/app_id] if app_id else [p for p in provider.iterdir() if p.is_dir() and p.name.isdecimal()]
                for app in apps:
                    for tail in TAILS:
                        add(app/tail)
    for env in ('APPDATA', 'LOCALAPPDATA'):
        if os.environ.get(env):
            for name in ('NBA 2K27', 'NBA2K27'):
                for parent in (Path(os.environ[env])/'2K Sports'/name, Path(os.environ[env])/name):
                    for tail in TAILS:
                        add(parent/tail)
    for parent in (game.parent, game.parent/'Profile', game.parent/'Saves'):
        for tail in TAILS:
            add(parent/tail)
    candidates = []
    rejected = 0
    for folder in folders.values():
        for manifest in available_manifests(folder['path'], settings['roster_path']):
            try:
                details, _, _, _ = inspect_native_roster(settings, folder['path'], manifest)
            except (OSError, ValueError, KeyError, StopIteration, zipfile.BadZipFile, zlib.error, struct.error):
                rejected += 1
                continue
            candidates.append(dict(**folder, manifest=manifest, players=details['players'],
                                   modified=Path(folder['path'], manifest).stat().st_mtime, verified=True))
    preferred = [i for i,c in enumerate(candidates) if same_path(c['path'], settings.get('sync_directory'))
                 and c['manifest'] == settings.get('manifest_name') and same_path(game, settings.get('game_executable'))]
    if not preferred:
        active = active_steam_user()
        preferred = [i for i,c in enumerate(candidates) if active and c['origin']=='steam' and c['account']==active]
    selected = preferred[0] if len(preferred)==1 else (0 if len(candidates)==1 else None)
    return dict(executable=str(game), launch_mode='steam' if steam else 'direct', app_id=app_id,
                candidates=candidates, selected=selected, rejected=rejected)


def automatic_storage(executable, sync_directory, manifest_name):
    identity='|'.join(str(Path(p).resolve()).casefold() for p in (executable, sync_directory))+'|'+manifest_name
    key=hashlib.sha256(identity.encode('utf-8')).hexdigest()[:16]
    data=recommended_data_dir()/'Installations'/key
    cache=(Path('E:/Cache/NBA-Roster-Sync') if Path('E:/').is_dir() else
           Path(os.environ.get('LOCALAPPDATA', Path.home()/'AppData/Local'))/'NBA-Roster-Sync/Cache')/key
    return dict(data_directory=str(data), cache_directory=str(cache), baseline_directory='')
