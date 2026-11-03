"""Synchronize all 30 NBA teams in the local SYNC roster, with no game UI.

The imported local game roster remains immutable. Each generated ZIP has its
content MD5 as its file name, matching the native manifest convention. The new
blob is verified first; replacing one manifest atomically commits the update.
"""
from __future__ import annotations

from i18n import localize,tr

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import zipfile
import shutil

import psutil

from fetch_source import CACHE_ROOT, SNAPSHOT_PATH, fetch
from roster_file import Roster
from nba_reconcile import update_roster, validate_roster
from app_runtime import load_settings, path_setting, validate_settings

def configure():
    global ROOT, BASE, DEST, MANIFEST, ROSTER_PATH, GAME, CACHE_ROOT, SNAPSHOT_PATH
    settings = load_settings()
    ROOT = path_setting(settings, 'data_directory')
    BASE = path_setting(settings, 'baseline_directory')
    DEST = Path(settings['sync_directory'])
    MANIFEST = settings['manifest_name']
    ROSTER_PATH = settings['roster_path']
    GAME = Path(settings['game_executable'])
    CACHE_ROOT = path_setting(settings, 'cache_directory')
    SNAPSHOT_PATH = CACHE_ROOT/'espn_snapshot.json'
    return settings


configure()


def digest(data):
    return hashlib.md5(data).hexdigest().upper()


def guid(data):
    h = digest(data)
    return '-'.join([h[:8], h[8:12], h[12:16], h[16:20], h[20:]])


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def game_running():
    name = Path(load_settings()['game_executable']).name.lower()
    return bool(name) and any((p.info['name'] or '').lower() == name
                              for p in psutil.process_iter(['name']))


def manifest_entries(data):
    result = {}
    text = data[:-1] if data.endswith(b'\0') else data
    if b'\0' in text:
        raise ValueError(localize('SYNC 清单内有非结尾的空字符'))
    for line in text.decode('utf-8').splitlines():
        name, blob, size = line.rsplit(' ', 2)
        if name in result:
            raise ValueError(localize('SYNC 清单包含重复路径'))
        if Path(blob).name != blob or not all(c in '0123456789abcdefABCDEF-' for c in blob):
            raise ValueError(localize('SYNC 清单的数据文件名无效'))
        result[name] = (blob, int(size))
    return result


def source_roster():
    entries = manifest_entries((BASE / MANIFEST).read_bytes())
    blob, size = entries[ROSTER_PATH]
    raw = (BASE / blob).read_bytes()
    if len(raw) != size or guid(raw) != blob:
        raise ValueError(localize('本机原生名单 ZIP 长度或 MD5 与清单不一致'))
    return unpack_roster(raw)


def unpack_roster(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if archive.namelist() != ['roster.RDAT']:
            raise ValueError(localize('基础名单 ZIP 内容改变'))
        info = archive.getinfo('roster.RDAT')
        if info.file_size > 256*1024*1024:
            raise ValueError(localize('基准名单解压大小超出支持范围'))
        data = archive.read(info)
    return data, info


def build(snapshot, output_directory, source):
    data, info = source
    if shutil.disk_usage(output_directory).free < len(data)*3 + 20*1024*1024:
        raise OSError(localize('缓存盘空间不足，请在设置中更换缓存目录'))
    source = output_directory / 'source.RDAT'
    source.write_bytes(data)
    roster = Roster(source)
    report = update_roster(roster, snapshot)
    updated = roster.rebuild()
    out = output_directory / 'updated.RDAT'
    out.write_bytes(updated)
    checked = Roster(out)  # Verifies every node checksum and all three schemas.
    validate_roster(checked, report)
    if checked.players.data != roster.players.data or checked.teams.data != roster.teams.data or checked.free_agents.data != roster.free_agents.data:
        raise ValueError(localize('生成文件的三张修改表回读不一致'))
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr(info, updated, compresslevel=4)
    blob = buffer.getvalue()
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        if archive.testzip() or archive.read('roster.RDAT') != updated:
            raise ValueError(localize('名单 ZIP 回读失败'))
    report['blob'] = guid(blob)
    report['bytes'] = len(blob)
    return blob, report


def synchronize(*, refresh=True, install=True):
    configure()
    validate_settings()
    if game_running():
        raise RuntimeError(localize('游戏正在运行；为避免覆盖已加载数据，本次不更新'))
    target = DEST / MANIFEST
    current = target.read_bytes()
    original = (BASE / MANIFEST).read_bytes()
    state_path = ROOT / 'last_sync.json'
    installation_id = hashlib.sha256((str(DEST.resolve()).casefold()+'|'+MANIFEST).encode('utf-8')).hexdigest()
    allowed = {hashlib.sha256(original).hexdigest()}
    if state_path.exists():
        previous_state = json.loads(state_path.read_text('utf-8'))
        if previous_state.get('installation_id', installation_id) != installation_id:
            raise RuntimeError(localize('当前数据目录属于另一个游戏存档位置，请为此安装选择独立的数据目录'))
        allowed.add(previous_state['manifest_sha256'])
    if hashlib.sha256(current).hexdigest() not in allowed:
        raise RuntimeError(localize('本地 SYNC 已被其他程序更新，停止覆盖并保留现有文件'))
    installed_source = (BASE/'baseline.json')
    if installed_source.is_file():
        meta = json.loads(installed_source.read_text('utf-8'))
        if meta['manifest_sha256'] != hashlib.sha256(original).hexdigest():
            raise ValueError(localize('本地基准名单已改变，请重新导入基准'))
    entries = manifest_entries(current)
    current_blob, current_size = entries[ROSTER_PATH]
    old = (DEST / current_blob).read_bytes()
    if guid(old) != current_blob or len(old) != current_size:
        raise ValueError(localize('已安装名单的 MD5 或长度校验失败'))
    # The current, recognized installed roster is the fallback anchor. The
    # immutable import is still validated and retained solely for recovery.
    source_roster()
    current_source=unpack_roster(old)
    from usage_notice import ensure_usage_consent
    ensure_usage_consent()
    snapshot = fetch() if refresh else json.loads(SNAPSHOT_PATH.read_text('utf-8'))
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='nba-', dir=CACHE_ROOT) as temporary:
        blob, report = build(snapshot, Path(temporary), current_source)
    report.update(fallback_source='current_installed_roster',planning_manifest_sha256=hashlib.sha256(current).hexdigest())
    if not install:
        return report
    if game_running():
        raise RuntimeError(localize('游戏已启动，本次不提交更新'))
    if target.read_bytes()!=current:
        raise RuntimeError(localize('规划期间游戏名单被其他程序改动，停止提交'))
    lines = []
    for line in current.rstrip(b'\0').decode('utf-8').splitlines():
        if line.rsplit(' ', 2)[0] == ROSTER_PATH:
            line = f'{ROSTER_PATH} {report["blob"]} {len(blob)}'
        lines.append(line)
    manifest = ('\n'.join(lines)+'\n').encode('utf-8') + (b'\0' if current.endswith(b'\0') else b'')
    backup = ROOT / 'Backups' / 'manifests' / (hashlib.sha256(current).hexdigest()+'.bin')
    if not backup.exists():
        atomic_write(backup, current)
    if current_blob != report['blob']:
        atomic_write(DEST / report['blob'], blob)
    if guid((DEST / report['blob']).read_bytes()) != report['blob']:
        raise ValueError(localize('落盘后的名单 MD5 校验失败'))
    report.update(manifest_sha256=hashlib.sha256(manifest).hexdigest(), installation_id=installation_id,
                  previous_blob=current_blob, installed=True,
                  game_validation='Runtime integrity checks completed. Fallback teams are reported separately; in-game presentation is not verified by this operation.')
    # Save the previous committed state for recovery if the final write fails.
    atomic_write(ROOT / 'pending_sync.json', json.dumps(report,ensure_ascii=False,indent=2).encode('utf-8'))
    try:
        if game_running():raise RuntimeError(localize('游戏已启动，本次不提交更新'))
        if target.read_bytes()!=current:raise RuntimeError(localize('规划期间游戏名单被其他程序改动，停止提交'))
        if manifest != current:
            atomic_write(target, manifest)
        atomic_write(state_path, json.dumps(report,ensure_ascii=False,indent=2).encode('utf-8'))
    except BaseException:
        if target.read_bytes()==manifest:atomic_write(target, current)
        raise
    finally:
        (ROOT / 'pending_sync.json').unlink(missing_ok=True)
    # Retain source data on every failed update; clear it only after commit.
    try:
        SNAPSHOT_PATH.unlink(missing_ok=True)
        for diagnostic in CACHE_ROOT.glob('depth-diagnostic-*.json'):
            suffix=diagnostic.stem.removeprefix('depth-diagnostic-')
            if len(suffix)==16 and all(c in '0123456789abcdef' for c in suffix) and not diagnostic.is_symlink():
                diagnostic.unlink()
    except OSError as error:
        print(tr('名单已更新，但来源缓存清理失败：{error}',error=localize(error)), file=sys.stderr)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cached', action='store_true', help='Use already fetched data, for validation')
    parser.add_argument('--preview', action='store_true', help='Build and validate without installing')
    args = parser.parse_args()
    result = synchronize(refresh=not args.cached, install=not args.preview)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(tr('更新失败，保留上次名单：{error}',error=localize(error)),file=sys.stderr)
        sys.exit(1)
