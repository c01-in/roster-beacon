"""Import only the user's native roster and restore the original manifest."""

from i18n import localize
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path
import tempfile
import zipfile

from app_runtime import load_profile, path_setting, validate_settings
from operations import operation_lock
from roster_file import Roster
import sync_nba as sync


def available_manifests(folder, roster_path='roster/roster.iff'):
    found = []
    for file in Path(folder).glob('manifest_*.bin'):
        try:
            if roster_path in sync.manifest_entries(file.read_bytes()):
                found.append(file.name)
        except (OSError, ValueError, UnicodeError):
            continue
    return sorted(found)


def inspect_native_roster(settings, source_folder=None, manifest_name=None):
    """Inspect existing data without changing game files or creating a backup."""
    source = Path(source_folder or settings['sync_directory']).resolve()
    manifest = manifest_name or settings['manifest_name']
    raw = (source/manifest).read_bytes()
    entries = sync.manifest_entries(raw)
    blob, size = entries[settings['roster_path']]
    payload = (source/blob).read_bytes()
    if len(payload) != size or sync.guid(payload) != blob:
        raise ValueError(localize('原生名单的长度或 MD5 与清单不符'))
    cache = path_setting(settings, 'cache_directory')
    cache.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        if archive.namelist() != ['roster.RDAT'] or archive.getinfo('roster.RDAT').file_size > 256*1024*1024:
            raise ValueError(localize('请选择原生 SYNC 名单；当前兼容档案仅支持单一 roster.RDAT ZIP'))
        data = archive.read('roster.RDAT')
    with tempfile.TemporaryDirectory(dir=cache, prefix='import-') as temporary:
        check = Path(temporary)/'roster.RDAT'
        check.write_bytes(data)
        roster = Roster(check, profile=load_profile(settings))
        details = dict(players=roster.players.count, teams=roster.teams.count,
                       layout=dict(players=roster.players.stride,teams=roster.teams.stride,free_agents=roster.free_agents.stride))
    return details, raw, payload, blob


def import_baseline(settings, source_folder=None):
    """Immutable baseline folders are named by original manifest SHA256."""
    details, raw, payload, blob = inspect_native_roster(settings, source_folder)
    manifest = settings['manifest_name']
    checksum = hashlib.sha256(raw).hexdigest()
    base = path_setting(settings, 'data_directory')/'Baselines'/checksum
    base.mkdir(parents=True, exist_ok=True)
    sync.atomic_write(base/blob, payload)
    sync.atomic_write(base/manifest, raw)
    sync.atomic_write(base/'baseline.json', json.dumps(dict(
        imported_at=datetime.now().astimezone().isoformat(), manifest_sha256=checksum,
        roster_blob=blob, profile=settings['compatibility_profile'], **details),
        ensure_ascii=False,indent=2).encode('utf-8'))
    settings['baseline_directory'] = str(base)
    return details


def restore_baseline():
    validate_settings()
    sync.configure()
    with operation_lock():
        if sync.game_running():
            raise RuntimeError(localize('请先正常退出游戏再恢复名单'))
        sync.source_roster()
        manifest = (sync.BASE/sync.MANIFEST).read_bytes()
        blob, size = sync.manifest_entries(manifest)[sync.ROSTER_PATH]
        target = sync.DEST/sync.MANIFEST
        current = target.read_bytes()
        from usage_notice import ensure_usage_consent
        ensure_usage_consent()
        if sync.game_running() or target.read_bytes()!=current:
            raise RuntimeError(localize('确认期间游戏已启动或名单已改变，已停止恢复'))
        saved = sync.ROOT/'Backups/manifests'/(hashlib.sha256(current).hexdigest()+'.bin')
        sync.atomic_write(saved, current)
        if not (sync.DEST/blob).is_file():
            sync.atomic_write(sync.DEST/blob, (sync.BASE/blob).read_bytes())
        elif sync.guid((sync.DEST/blob).read_bytes()) != blob:
            raise ValueError(localize('游戏目录中的基准 ZIP 校验失败，已停止恢复'))
        sync.atomic_write(target, manifest)
        return dict(restored=True, manifest_sha256=hashlib.sha256(manifest).hexdigest(),
                    baseline=str(sync.BASE), backup=str(saved))
